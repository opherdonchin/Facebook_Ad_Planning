from dataclasses import dataclass
from typing import Callable, Dict
import pandas as pd
import ibis

# -------------------------
# Transform type
# -------------------------

TransformFn = Callable[[Dict[str, ibis.expr.types.Table]], pd.DataFrame]

# -------------------------
# Transform spec
# -------------------------


@dataclass(frozen=True)
class TransformSpec:
    name: str
    transform: TransformFn
    input_tables: Dict[str, str]  # alias -> Grist table id
    output_table: str
    overwrite: bool = True
    # mapping of input_alias -> { raw_column: canonical_column }
    select_rename: Dict[str, Dict[str, str]] = None


# -------------------------
# Transforms
# -------------------------


def weekly_metrics_joined_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    t_runs = tables["perf"]
    t_ads = tables["ads"]

    # Canonical inputs:
    # perf: Week, Ad_id, Spend, Leads, Intended_run
    # ads: id, Name, Campaign

    joined = t_runs.join(t_ads, t_runs["Ad_id"] == t_ads["id"])

    # Group by canonical names
    g = joined.group_by(
        [t_runs["Week"], t_ads["Campaign"], t_ads["Name"].name("Ad")]
    ).aggregate(
        Spend=t_runs["Spend"].sum(),
        Leads=t_runs["Leads"].sum(),
        Intended_run=ibis.coalesce(t_runs["Intended_run"], False).any(),
    )

    # Calculate metrics
    g = g.mutate(CPL=ibis.ifelse(g["Leads"] > 0, g["Spend"] / g["Leads"], ibis.null()))

    g = g.mutate(
        Flag_NoLeads=ibis.ifelse(g["Leads"] == 0, True, False),
        Flag_LowSample=ibis.ifelse(g["Leads"] < 3, True, False),
    )

    return g.execute()


def lifetime_ad_metrics_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    t_runs = tables["perf"]
    t_ads = tables["ads"]

    # Canonical inputs:
    # perf: Week, Ad_id, Spend, Leads
    # ads: id, Name, Campaign

    # 1. Aggregate Weekly_runs by Ad_id
    # Note: Weeks is count distinct of Week
    metrics = t_runs.group_by(t_runs["Ad_id"]).aggregate(
        Spend=t_runs["Spend"].sum(),
        Leads=t_runs["Leads"].sum(),
        Weeks=t_runs["Week"].nunique(),
        FirstWeek=t_runs["Week"].min(),
        LastWeek=t_runs["Week"].max(),
    )

    # 2. Join to Ads for metadata
    joined = metrics.join(t_ads, metrics["Ad_id"] == t_ads["id"])

    # 3. Project and formatting
    res = joined.select(
        t_ads["Campaign"],
        t_ads["Name"].name("Ad"),
        metrics["Spend"],
        metrics["Leads"],
        metrics["Weeks"],
        metrics["FirstWeek"],
        metrics["LastWeek"],
    )

    # Calculate CPL
    res = res.mutate(
        CPL=ibis.ifelse(res["Leads"] > 0, res["Spend"] / res["Leads"], ibis.null())
    )

    return res.execute()


def last_contiguous_run_ad_metrics_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    import re
    import pandas as pd

    t_runs = tables["perf"]
    t_ads = tables["ads"]

    runs = t_runs.select("Week", "Ad_id", "Spend", "Leads").execute()
    ads = t_ads.select("id", "Name", "Campaign").execute()

    cols = [
        "Campaign",
        "Ad",
        "Week_last_run_start",
        "Week_last_run_end",
        "Weeks_in_last_run",
        "Spend_last_run",
        "Leads_last_run",
        "CPL_last_run",
    ]
    if runs.empty:
        return pd.DataFrame(columns=cols)

    # --- Normalize + parse Week labels robustly ---
    w = runs["Week"].astype(str).str.strip()

    # Normalize common Unicode hyphens/dashes to ASCII "-"
    w = w.replace(
        {
            "\u2010": "-",  # hyphen
            "\u2011": "-",  # non-breaking hyphen
            "\u2012": "-",  # figure dash
            "\u2013": "-",  # en dash
            "\u2014": "-",  # em dash
            "\u2212": "-",  # minus sign
        },
        regex=True,
    )

    # Extract ISO year/week (accepts "YYYY-W1" or "YYYY-W01")
    m = w.str.extract(r"^(?P<y>\d{4})-W(?P<w>\d{1,2})$", expand=True)

    # If parsing fails for too many rows, fail loudly
    bad = m["y"].isna() | m["w"].isna()
    if bad.any():
        # Keep the failure noisy but not catastrophic for a tiny number of bad rows
        n_bad = int(bad.sum())
        if n_bad > 0:
            examples = w[bad].head(5).tolist()
            raise ValueError(
                f"Unparseable Week labels: {n_bad} rows. Examples: {examples}. "
                "Expected format like '2026-W01' or '2026-W1'."
            )

    iso_year = m["y"].astype(int)
    iso_week = m["w"].astype(int)

    # Build canonical padded string "YYYY-Www"
    week_canon = iso_year.astype(str) + "-W" + iso_week.astype(str).str.zfill(2)

    # Monday of ISO week: format needs "YYYY-Www-1"
    week_monday = pd.to_datetime(week_canon + "-1", format="%G-W%V-%u", errors="raise")

    runs = runs.copy()
    runs["Week_canon"] = week_canon
    runs["Week_monday"] = week_monday

    # Optional delivery definition: uncomment if you only want weeks with actual delivery
    # runs = runs[(runs["Spend"] > 0) | (runs["Leads"] > 0)]

    # Aggregate to one row per (Ad_id, Week_monday) to eliminate duplicates
    runs_w = (
        runs.groupby(["Ad_id", "Week_monday", "Week_canon"], as_index=False)
        .agg(Spend=("Spend", "sum"), Leads=("Leads", "sum"))
        .sort_values(["Ad_id", "Week_monday"])
    )

    out_rows = []
    for ad_id, g in runs_w.groupby("Ad_id", sort=False):
        g = g.sort_values("Week_monday").reset_index(drop=True)

        # Contiguous blocks: exactly 7-day steps
        gaps = g["Week_monday"].diff().dt.days
        new_block = gaps.isna() | (gaps != 7)
        block_id = new_block.cumsum()

        last_block = block_id.iloc[-1]
        last = g[block_id == last_block]

        spend = float(last["Spend"].sum())
        leads = float(last["Leads"].sum())
        cpl = (spend / leads) if leads > 0 else None

        out_rows.append(
            {
                "Ad_id": ad_id,
                "Week_last_run_start": last["Week_canon"].iloc[0],
                "Week_last_run_end": last["Week_canon"].iloc[-1],
                "Weeks_in_last_run": int(len(last)),
                "Spend_last_run": spend,
                "Leads_last_run": (
                    int(round(leads)) if abs(leads - round(leads)) < 1e-9 else leads
                ),
                "CPL_last_run": cpl,
            }
        )

    out = pd.DataFrame(out_rows)

    # Join Ads metadata
    out = out.merge(ads, left_on="Ad_id", right_on="id", how="left")

    out = (
        out.rename(columns={"Name": "Ad"})
        .loc[:, cols]
        .sort_values(["Campaign", "Ad"], kind="stable")
        .reset_index(drop=True)
    )

    return out


def lifetime_ad_conversions_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    """
    Build lifetime conversion rollups by (Campaign, Ad) from:
      - leads: id, Campaign, Ad, Status
      - events: Lead_id, Event
    Counts are unique leads (not events).
    """

    t_leads = tables["leads"]
    t_events = tables["events"]

    # 1) Per-lead event flags
    # Note: ibis.any(...) is an aggregate boolean "any true in group"
    events_by_lead = t_events.group_by(t_events["Lead_id"]).aggregate(
        Has_Trial=(t_events["Event"] == "Introductory lesson").any(),
        Has_Registration=(t_events["Event"] == "Registration").any(),
    )

    # 2) Join flags onto leads (left join so leads with no events are kept)
    leads_enriched = (
        t_leads.join(
            events_by_lead, t_leads["id"] == events_by_lead["Lead_id"], how="left"
        )
        .mutate(
            Has_Trial=lambda t: ibis.coalesce(t.Has_Trial, False),
            Has_Registration=lambda t: ibis.coalesce(t.Has_Registration, False),
        )
        .mutate(
            # Failed means explicitly failed AND never registered
            Is_Failed=lambda t: (t.Status == "Failed")
            & ~t.Has_Registration
        )
    )

    # 3) Filter to leads that actually have attribution fields populated
    # (prevents counting blank/unknown Campaign/Ad as a group)
    attributed = (
        leads_enriched.filter(lambda t: t.Campaign.notnull())
        .filter(lambda t: t.Campaign != "")
        .filter(lambda t: t.Ad.notnull())
        .filter(lambda t: t.Ad != "")
    )

    # 4) Aggregate by (Campaign, Ad)
    g = attributed.group_by([attributed["Campaign"], attributed["Ad"]]).aggregate(
        Leads_Attributed=attributed["id"].nunique(),
        Leads_With_Trial=attributed["Has_Trial"].cast("int").sum(),
        Leads_Registered=attributed["Has_Registration"].cast("int").sum(),
        Leads_Failed=attributed["Is_Failed"].cast("int").sum(),
    )

    # 5) Rates (denominator is attributed leads from Leads table)
    g = g.mutate(
        Trial_Conversion_Rate=ibis.ifelse(
            g["Leads_Attributed"] > 0,
            g["Leads_With_Trial"] / g["Leads_Attributed"],
            ibis.null(),
        ),
        Registration_Conversion_Rate=ibis.ifelse(
            g["Leads_Attributed"] > 0,
            g["Leads_Registered"] / g["Leads_Attributed"],
            ibis.null(),
        ),
        Failure_Rate=ibis.ifelse(
            g["Leads_Attributed"] > 0,
            g["Leads_Failed"] / g["Leads_Attributed"],
            ibis.null(),
        ),
    )

    # Optional: reorder columns for readability
    g = g.select(
        "Campaign",
        "Ad",
        "Leads_Attributed",
        "Leads_With_Trial",
        "Trial_Conversion_Rate",
        "Leads_Registered",
        "Registration_Conversion_Rate",
        "Leads_Failed",
        "Failure_Rate",
    )

    return g.execute()


def tag_lifetime_rollups_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    # Inputs
    t_perf = tables["perf"]
    t_ads = tables["ads"]
    t_creatives = tables["creatives"]
    t_media = tables["media"]
    t_headlines = tables["headlines"]
    t_texts = tables["texts"]

    # Dictionaries
    d_style = tables["media_style"]
    d_energy = tables["media_energy"]
    d_tone = tables["tone"]
    d_promise = tables["promise_types"]
    d_hook = tables["hook_types"]

    # 1. Build Spine
    # Use uniquely named IDs (from select_rename) to avoid join collisions in Ibis

    spine = (
        t_perf.join(t_ads, t_perf["Ad_id"] == t_ads["ad_oid"])
        .join(t_creatives, t_ads["Creative_id"] == t_creatives["creative_oid"])
        .join(t_media, t_creatives["Media_id"] == t_media["media_oid"])
        .join(t_headlines, t_creatives["Headline_id"] == t_headlines["headline_oid"])
        .join(t_texts, t_ads["Text_id"] == t_texts["text_oid"])
    )

    # Helper to aggregate by a tag column
    def agg_by_tag(spine_table, tag_col_expr, dim_name):
        return (
            spine_table.group_by(tag_col_expr.name("Tag"))
            .aggregate(
                Spend=spine_table["Spend"].sum(),
                Leads=spine_table["Leads"].sum(),
                Ads=spine_table["Ad_id"].nunique(),
                Weeks=spine_table["Week"].nunique(),
            )
            .mutate(
                Tag_Dimension=ibis.literal(dim_name),
                CPL=lambda t: ibis.ifelse(t.Leads > 0, t.Spend / t.Leads, ibis.null()),
            )
            # Filter null tags
            .filter(lambda t: t.Tag.notnull())
            .filter(lambda t: t.Tag != "")
            .select("Tag_Dimension", "Tag", "Spend", "Leads", "CPL", "Ads", "Weeks")
        )

    unions = []

    # 1. Media_Style
    s_style = spine.join(d_style, spine["Media_Style_id"] == d_style["style_oid"])
    unions.append(agg_by_tag(s_style, d_style["Media_Style"], "Media_Style"))

    # 2. Media_Energy
    s_en = spine.join(d_energy, spine["Media_Energy_id"] == d_energy["energy_oid"])
    unions.append(agg_by_tag(s_en, d_energy["Media_Energy"], "Media_Energy"))

    # 3. Headline_Tone
    s_tone = spine.join(d_tone, spine["Tone_id"] == d_tone["tone_oid"])
    unions.append(agg_by_tag(s_tone, d_tone["Tone"], "Headline_Tone"))

    # 4. Headline_Promise
    s_hp = spine.join(
        d_promise, spine["Promise_id_headline"] == d_promise["promise_oid"]
    )
    unions.append(agg_by_tag(s_hp, d_promise["Promise"], "Headline_Promise"))

    # 5. Headline_Hook
    s_hh = spine.join(d_hook, spine["Hooks_id"] == d_hook["hook_oid"])
    unions.append(agg_by_tag(s_hh, d_hook["Hook"], "Headline_Hook"))

    # 6. Text_Hook
    s_th = spine.join(d_hook, spine["Hook_id_text"] == d_hook["hook_oid"])
    unions.append(agg_by_tag(s_th, d_hook["Hook"], "Text_Hook"))

    # 7. Text_Promise
    s_tp = spine.join(d_promise, spine["Promise_id_text"] == d_promise["promise_oid"])
    unions.append(agg_by_tag(s_tp, d_promise["Promise"], "Text_Promise"))

    # 8. Text_Structure (String, no join)
    unions.append(agg_by_tag(spine, spine["Structure"], "Text_Structure"))

    return ibis.union(*unions).execute()


def component_media_lifetime_metrics_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    """
    Aggregate lifetime metrics by Media component.
    Sums Spend and Leads for all ads using each media asset, then calculates CPL.
    """
    t_runs = tables["perf"]
    t_ads = tables["ads"]
    t_creatives = tables["creatives"]
    t_media = tables["media"]

    # Join runs to ads to creatives to media
    joined = (
        t_runs.join(t_ads, t_runs["Ad_id"] == t_ads["ad_oid"])
        .join(t_creatives, t_ads["Creative_id"] == t_creatives["creative_oid"])
        .join(t_media, t_creatives["Media_id"] == t_media["media_oid"])
    )

    # Aggregate by media ID
    agg = joined.group_by(t_media["media_oid"].name("Media_ID")).aggregate(
        Name=t_media["Name"].first(),
        Variant=t_media["Variant"].first(),
        Format=t_media["Format"].first(),
        Spend=t_runs["Spend"].sum(),
        Leads=t_runs["Leads"].sum(),
        Ads=t_ads["ad_oid"].nunique(),
    )

    # Calculate CPL
    agg = agg.mutate(
        CPL=ibis.ifelse(agg["Leads"] > 0, agg["Spend"] / agg["Leads"], ibis.null())
    )

    # Execute and sort in pandas (nulls last)
    result_df = agg.execute()
    result_df = result_df.sort_values(
        by=["CPL", "Spend"], ascending=[True, False], na_position="last"
    )

    return result_df


def component_headline_lifetime_metrics_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    """
    Aggregate lifetime metrics by Headline component.
    Sums Spend and Leads for all ads using each headline, then calculates CPL.
    """
    t_runs = tables["perf"]
    t_ads = tables["ads"]
    t_creatives = tables["creatives"]
    t_headlines = tables["headlines"]

    # Join runs to ads to creatives to headlines
    joined = (
        t_runs.join(t_ads, t_runs["Ad_id"] == t_ads["ad_oid"])
        .join(t_creatives, t_ads["Creative_id"] == t_creatives["creative_oid"])
        .join(t_headlines, t_creatives["Headline_id"] == t_headlines["headline_oid"])
    )

    # Aggregate by headline ID
    agg = joined.group_by(t_headlines["headline_oid"].name("Headline_ID")).aggregate(
        Text=t_headlines["Text"].first(),
        Spend=t_runs["Spend"].sum(),
        Leads=t_runs["Leads"].sum(),
        Ads=t_ads["ad_oid"].nunique(),
    )

    # Calculate CPL
    agg = agg.mutate(
        CPL=ibis.ifelse(agg["Leads"] > 0, agg["Spend"] / agg["Leads"], ibis.null())
    )

    # Execute and sort in pandas (nulls last)
    result_df = agg.execute()
    result_df = result_df.sort_values(
        by=["CPL", "Spend"], ascending=[True, False], na_position="last"
    )

    return result_df


def component_text_lifetime_metrics_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    """
    Aggregate lifetime metrics by Text component.
    Sums Spend and Leads for all ads using each text, then calculates CPL.
    """
    t_runs = tables["perf"]
    t_ads = tables["ads"]
    t_texts = tables["texts"]

    # Join runs to ads to texts
    joined = t_runs.join(t_ads, t_runs["Ad_id"] == t_ads["ad_oid"]).join(
        t_texts, t_ads["Text_id"] == t_texts["text_oid"]
    )

    # Aggregate by text ID
    agg = joined.group_by(t_texts["text_oid"].name("Text_ID")).aggregate(
        Name=t_texts["Name"].first(),
        Variant=t_texts["Variant"].first(),
        Primary_text=t_texts["Primary_text"].first(),
        Spend=t_runs["Spend"].sum(),
        Leads=t_runs["Leads"].sum(),
        Ads=t_ads["ad_oid"].nunique(),
    )

    # Calculate CPL
    agg = agg.mutate(
        CPL=ibis.ifelse(agg["Leads"] > 0, agg["Spend"] / agg["Leads"], ibis.null())
    )

    # Execute and sort in pandas (nulls last)
    result_df = agg.execute()
    result_df = result_df.sort_values(
        by=["CPL", "Spend"], ascending=[True, False], na_position="last"
    )

    return result_df


def component_tags_transform(
    tables: Dict[str, ibis.expr.types.Table],
) -> pd.DataFrame:
    """
    Create a component × tag junction table.
    Returns one row per component × tag combination with component metadata.
    """
    t_media = tables["media"]
    t_headlines = tables["headlines"]
    t_texts = tables["texts"]

    # Dictionaries
    d_style = tables["media_style"]
    d_energy = tables["media_energy"]
    d_tone = tables["tone"]
    d_promise = tables["promise_types"]
    d_hook = tables["hook_types"]

    rows = []

    # Media components
    media_df = t_media.execute()
    for _, row in media_df.iterrows():
        component_id = row["media_oid"]
        component_name = row.get("Name", "")

        # Media_Style tag
        if pd.notna(row.get("Media_Style_id")):
            style_row = d_style.filter(
                d_style["style_oid"] == row["Media_Style_id"]
            ).execute()
            if not style_row.empty:
                rows.append(
                    {
                        "component_type": "media",
                        "component_id": component_id,
                        "component_name": component_name,
                        "tag_type": "Media_Style",
                        "tag_value": style_row.iloc[0]["Media_Style"],
                    }
                )

        # Media_Energy tag
        if pd.notna(row.get("Media_Energy_id")):
            energy_row = d_energy.filter(
                d_energy["energy_oid"] == row["Media_Energy_id"]
            ).execute()
            if not energy_row.empty:
                rows.append(
                    {
                        "component_type": "media",
                        "component_id": component_id,
                        "component_name": component_name,
                        "tag_type": "Media_Energy",
                        "tag_value": energy_row.iloc[0]["Media_Energy"],
                    }
                )

    # Headline components
    headline_df = t_headlines.execute()
    for _, row in headline_df.iterrows():
        component_id = row["headline_oid"]
        component_name = row.get("Text", "")

        # Tone tag
        if pd.notna(row.get("Tone_id")):
            tone_row = d_tone.filter(d_tone["tone_oid"] == row["Tone_id"]).execute()
            if not tone_row.empty:
                rows.append(
                    {
                        "component_type": "headline",
                        "component_id": component_id,
                        "component_name": component_name,
                        "tag_type": "Tone",
                        "tag_value": tone_row.iloc[0]["Tone"],
                    }
                )

        # Promise tag
        if pd.notna(row.get("Promise_id_headline")):
            promise_row = d_promise.filter(
                d_promise["promise_oid"] == row["Promise_id_headline"]
            ).execute()
            if not promise_row.empty:
                rows.append(
                    {
                        "component_type": "headline",
                        "component_id": component_id,
                        "component_name": component_name,
                        "tag_type": "Promise",
                        "tag_value": promise_row.iloc[0]["Promise"],
                    }
                )

        # Hooks tag
        if pd.notna(row.get("Hooks_id")):
            hook_row = d_hook.filter(d_hook["hook_oid"] == row["Hooks_id"]).execute()
            if not hook_row.empty:
                rows.append(
                    {
                        "component_type": "headline",
                        "component_id": component_id,
                        "component_name": component_name,
                        "tag_type": "Hook",
                        "tag_value": hook_row.iloc[0]["Hook"],
                    }
                )

    # Text components
    text_df = t_texts.execute()
    for _, row in text_df.iterrows():
        component_id = row["text_oid"]
        component_name = row.get("Name", "")

        # Hook tag
        if pd.notna(row.get("Hook_id_text")):
            hook_row = d_hook.filter(
                d_hook["hook_oid"] == row["Hook_id_text"]
            ).execute()
            if not hook_row.empty:
                rows.append(
                    {
                        "component_type": "text",
                        "component_id": component_id,
                        "component_name": component_name,
                        "tag_type": "Hook",
                        "tag_value": hook_row.iloc[0]["Hook"],
                    }
                )

        # Promise tag
        if pd.notna(row.get("Promise_id_text")):
            promise_row = d_promise.filter(
                d_promise["promise_oid"] == row["Promise_id_text"]
            ).execute()
            if not promise_row.empty:
                rows.append(
                    {
                        "component_type": "text",
                        "component_id": component_id,
                        "component_name": component_name,
                        "tag_type": "Promise",
                        "tag_value": promise_row.iloc[0]["Promise"],
                    }
                )

        # Structure tag (string field, no join needed)
        if pd.notna(row.get("Structure")) and row["Structure"] != "":
            rows.append(
                {
                    "component_type": "text",
                    "component_id": component_id,
                    "component_name": component_name,
                    "tag_type": "Structure",
                    "tag_value": row["Structure"],
                }
            )

    return pd.DataFrame(rows)


# -------------------------
# Registry
# -------------------------

TRANSFORMS: Dict[str, TransformSpec] = {
    "weekly_metrics_prod": TransformSpec(
        name="weekly_metrics_prod",
        transform=weekly_metrics_joined_transform,
        input_tables={
            "perf": "Weekly_runs",
            "ads": "Ads",
        },
        output_table="Derived_Weekly_Ad_Metrics",
        overwrite=True,
        select_rename={
            "perf": {
                "A": "Week",
                "Ad": "Ad_id",
                "Spend": "Spend",
                "Leads": "Leads",
                "Intended_run": "Intended_run",
            },
            "ads": {
                "id": "id",
                "Name": "Name",
                "Campaign": "Campaign",
            },
        },
    ),
    "last_contiguous_run_ad_metrics_prod": TransformSpec(
        name="last_contiguous_run_ad_metrics_prod",
        transform=last_contiguous_run_ad_metrics_transform,
        input_tables={"perf": "Weekly_runs", "ads": "Ads"},
        output_table="Derived_Last_Run_Ad_Metrics",
        overwrite=True,
        select_rename={
            "perf": {"A": "Week", "Ad": "Ad_id", "Spend": "Spend", "Leads": "Leads"},
            "ads": {"id": "id", "Name": "Name", "Campaign": "Campaign"},
        },
    ),
    "lifetime_ad_metrics_prod": TransformSpec(
        name="lifetime_ad_metrics_prod",
        transform=lifetime_ad_metrics_transform,
        input_tables={
            "perf": "Weekly_runs",
            "ads": "Ads",
        },
        output_table="Derived_Lifetime_Ad_Metrics",
        overwrite=True,
        select_rename={
            "perf": {
                "A": "Week",
                "Ad": "Ad_id",
                "Spend": "Spend",
                "Leads": "Leads",
            },
            "ads": {
                "id": "id",
                "Name": "Name",
                "Campaign": "Campaign",
            },
        },
    ),
    "lifetime_ad_conversions_prod": TransformSpec(
        name="lifetime_ad_conversions_prod",
        transform=lifetime_ad_conversions_transform,
        input_tables={
            "leads": "Leads",
            "events": "Sales_events",
        },
        output_table="Derived_Lifetime_Ad_Conversions",
        overwrite=True,
        select_rename={
            "leads": {
                "id": "id",
                "Campaign": "Campaign",
                "Ad_name": "Ad",
                "Status": "Status",
            },
            "events": {
                "Name": "Lead_id",
                "Event": "Event",
            },
        },
    ),
    "tag_lifetime_rollups_prod": TransformSpec(
        name="tag_lifetime_rollups_prod",
        transform=tag_lifetime_rollups_transform,
        input_tables={
            "perf": "Weekly_runs",
            "ads": "Ads",
            "creatives": "Creatives",
            "media": "Media",
            "headlines": "Headlines",
            "texts": "Texts",
            "media_style": "Media_Style",
            "media_energy": "Media_Energy",
            "tone": "Tone",
            "promise_types": "Promise_types",
            "hook_types": "Hook_types",
        },
        output_table="Derived_Tag_Lifetime_Rollups",
        overwrite=True,
        select_rename={
            "perf": {
                "A": "Week",
                "Ad": "Ad_id",
                "Spend": "Spend",
                "Leads": "Leads",
            },
            "ads": {
                "id": "ad_oid",
                "Creative": "Creative_id",
                "Text": "Text_id",
            },
            "creatives": {
                "id": "creative_oid",
                "Media": "Media_id",
                "Headline": "Headline_id",
            },
            "media": {
                "id": "media_oid",
                "Media_Style": "Media_Style_id",
                "Media_Energy": "Media_Energy_id",
            },
            "headlines": {
                "id": "headline_oid",
                "Tone": "Tone_id",
                "Promise": "Promise_id_headline",
                "Hooks": "Hooks_id",
            },
            "texts": {
                "id": "text_oid",
                "Hook": "Hook_id_text",
                "Promise": "Promise_id_text",
                "Structure": "Structure",
            },
            "media_style": {"id": "style_oid", "Media_Style": "Media_Style"},
            "media_energy": {"id": "energy_oid", "Media_Energy": "Media_Energy"},
            "tone": {"id": "tone_oid", "Tone": "Tone"},
            "promise_types": {"id": "promise_oid", "Promise": "Promise"},
            "hook_types": {"id": "hook_oid", "Hook": "Hook"},
        },
    ),
    "component_media_lifetime_metrics_prod": TransformSpec(
        name="component_media_lifetime_metrics_prod",
        transform=component_media_lifetime_metrics_transform,
        input_tables={
            "perf": "Weekly_runs",
            "ads": "Ads",
            "creatives": "Creatives",
            "media": "Media",
        },
        output_table="Derived_Component_Media_Lifetime",
        overwrite=True,
        select_rename={
            "perf": {
                "A": "Week",
                "Ad": "Ad_id",
                "Spend": "Spend",
                "Leads": "Leads",
            },
            "ads": {
                "id": "ad_oid",
                "Creative": "Creative_id",
            },
            "creatives": {
                "id": "creative_oid",
                "Media": "Media_id",
            },
            "media": {
                "id": "media_oid",
                "Name": "Name",
                "Variant": "Variant",
                "Format": "Format",
            },
        },
    ),
    "component_headline_lifetime_metrics_prod": TransformSpec(
        name="component_headline_lifetime_metrics_prod",
        transform=component_headline_lifetime_metrics_transform,
        input_tables={
            "perf": "Weekly_runs",
            "ads": "Ads",
            "creatives": "Creatives",
            "headlines": "Headlines",
        },
        output_table="Derived_Component_Headline_Lifetime",
        overwrite=True,
        select_rename={
            "perf": {
                "A": "Week",
                "Ad": "Ad_id",
                "Spend": "Spend",
                "Leads": "Leads",
            },
            "ads": {
                "id": "ad_oid",
                "Creative": "Creative_id",
            },
            "creatives": {
                "id": "creative_oid",
                "Headline": "Headline_id",
            },
            "headlines": {
                "id": "headline_oid",
                "Text": "Text",
            },
        },
    ),
    "component_text_lifetime_metrics_prod": TransformSpec(
        name="component_text_lifetime_metrics_prod",
        transform=component_text_lifetime_metrics_transform,
        input_tables={
            "perf": "Weekly_runs",
            "ads": "Ads",
            "texts": "Texts",
        },
        output_table="Derived_Component_Text_Lifetime",
        overwrite=True,
        select_rename={
            "perf": {
                "A": "Week",
                "Ad": "Ad_id",
                "Spend": "Spend",
                "Leads": "Leads",
            },
            "ads": {
                "id": "ad_oid",
                "Text": "Text_id",
            },
            "texts": {
                "id": "text_oid",
                "Name": "Name",
                "Variant": "Variant",
                "Primary_text": "Primary_text",
            },
        },
    ),
    "component_tags_prod": TransformSpec(
        name="component_tags_prod",
        transform=component_tags_transform,
        input_tables={
            "media": "Media",
            "headlines": "Headlines",
            "texts": "Texts",
            "media_style": "Media_Style",
            "media_energy": "Media_Energy",
            "tone": "Tone",
            "promise_types": "Promise_types",
            "hook_types": "Hook_types",
        },
        output_table="Derived_Component_Tags",
        overwrite=True,
        select_rename={
            "media": {
                "id": "media_oid",
                "Name": "Name",
                "Media_Style": "Media_Style_id",
                "Media_Energy": "Media_Energy_id",
            },
            "headlines": {
                "id": "headline_oid",
                "Text": "Text",
                "Tone": "Tone_id",
                "Promise": "Promise_id_headline",
                "Hooks": "Hooks_id",
            },
            "texts": {
                "id": "text_oid",
                "Name": "Name",
                "Hook": "Hook_id_text",
                "Promise": "Promise_id_text",
                "Structure": "Structure",
            },
            "media_style": {"id": "style_oid", "Media_Style": "Media_Style"},
            "media_energy": {"id": "energy_oid", "Media_Energy": "Media_Energy"},
            "tone": {"id": "tone_oid", "Tone": "Tone"},
            "promise_types": {"id": "promise_oid", "Promise": "Promise"},
            "hook_types": {"id": "hook_oid", "Hook": "Hook"},
        },
    ),
}

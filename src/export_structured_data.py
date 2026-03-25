"""
Convert performance_data.json to structured Parquet files for ChatGPT analysis.

Reads the Grist database export and generates 8 tables:
1. ad_weekly_performance.parquet - Weekly performance by ad
2. ad_run_summary.parquet - Metrics per contiguous run
3. ad_lifetime_summary.parquet - Lifetime metrics by ad
4. ad_components.parquet - Ad-to-component mapping
5. component_media_lifetime.parquet - Lifetime metrics by media component
6. component_headline_lifetime.parquet - Lifetime metrics by headline component
7. component_text_lifetime.parquet - Lifetime metrics by text component
8. component_tags.parquet - Component-to-tag junction table
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any


def map_campaign_to_letter(campaign_series: pd.Series) -> pd.Series:
    """
    Map campaign numbers to letters: 1 -> 'W' (Women), 2 -> 'M' (Men).
    Handles both int and string inputs.
    """

    def convert_value(val):
        if pd.isna(val):
            return val
        # Convert to int first to handle both "1" and 1
        try:
            val_int = int(val)
            if val_int == 1:
                return "W"
            elif val_int == 2:
                return "M"
            else:
                return str(val)  # Keep original if not 1 or 2
        except (ValueError, TypeError):
            return str(val)  # Keep original if can't convert

    return campaign_series.apply(convert_value)


def load_performance_data(json_path: str) -> Dict[str, Any]:
    """Load the performance_data.json export."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_table_df(data: Dict[str, Any], table_name: str) -> pd.DataFrame:
    """Extract a table from the JSON structure and convert to DataFrame."""
    if table_name not in data["tables"]:
        raise ValueError(f"Table '{table_name}' not found in performance data")

    table = data["tables"][table_name]
    records = table["records"]

    if not records:
        return pd.DataFrame()

    # Records have structure: {"id": <id>, "fields": {<field_name>: <value>, ...}}
    # Flatten to: {"id": <id>, <field_name>: <value>, ...}
    flattened_records = []
    for record in records:
        flat = {"id": record["id"]}
        flat.update(record.get("fields", {}))
        flattened_records.append(flat)

    return pd.DataFrame(flattened_records)


def derive_weekly_intended_run_flags(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Build per-week intended-run flags from Weekly_runs.Intended_run.

    This keeps ad_weekly_performance.csv usable even before the derived Grist
    weekly metrics table is regenerated with an explicit intended-run column.
    """
    if "Weekly_runs" not in data["tables"] or "Ads" not in data["tables"]:
        return pd.DataFrame(
            columns=["iso_week", "campaign", "ad_name", "intended_run"]
        )

    weekly_runs = extract_table_df(data, "Weekly_runs")
    ads = extract_table_df(data, "Ads")

    if (
        weekly_runs.empty
        or ads.empty
        or "A" not in weekly_runs.columns
        or "Ad" not in weekly_runs.columns
        or "Intended_run" not in weekly_runs.columns
        or "Name" not in ads.columns
        or "Campaign" not in ads.columns
    ):
        return pd.DataFrame(
            columns=["iso_week", "campaign", "ad_name", "intended_run"]
        )

    intended_run_flags = (
        weekly_runs.loc[:, ["A", "Ad", "Intended_run"]]
        .rename(
            columns={
                "A": "iso_week",
                "Ad": "ad_id",
                "Intended_run": "intended_run",
            }
        )
        .merge(
            ads.loc[:, ["id", "Name", "Campaign"]].rename(
                columns={"id": "ad_id", "Name": "ad_name", "Campaign": "campaign"}
            ),
            on="ad_id",
            how="left",
        )
    )

    intended_run_flags["campaign"] = map_campaign_to_letter(
        intended_run_flags["campaign"]
    )
    intended_run_flags["intended_run"] = (
        intended_run_flags["intended_run"].fillna(False).astype(bool)
    )

    intended_run_flags = intended_run_flags.groupby(
        ["iso_week", "campaign", "ad_name"], as_index=False, sort=False
    ).agg(intended_run=("intended_run", "any"))

    return intended_run_flags


def generate_ad_weekly_performance(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate ad_weekly_performance table from Derived_Weekly_Ad_Metrics.

    Grain: one row per ad × ISO week
    """
    df = extract_table_df(data, "Derived_Weekly_Ad_Metrics")

    if df.empty:
        return pd.DataFrame(
            columns=[
                "iso_week",
                "campaign",
                "ad_name",
                "spend",
                "leads",
                "cpl",
                "intended_run",
            ]
        )

    result = pd.DataFrame(
        {
            "iso_week": (
                df.get("Week") if "Week" in df.columns else pd.Series(dtype=str)
            ),
            "campaign": map_campaign_to_letter(
                df.get("Campaign") if "Campaign" in df.columns else pd.Series(dtype=str)
            ),
            "ad_name": df.get("Ad") if "Ad" in df.columns else pd.Series(dtype=str),
            "spend": pd.to_numeric(
                df.get("Spend") if "Spend" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
            "leads": pd.to_numeric(
                df.get("Leads") if "Leads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "cpl": pd.to_numeric(
                df.get("CPL") if "CPL" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
        }
    )

    if "Intended_run" in df.columns:
        result["intended_run"] = pd.Series(
            df.get("Intended_run"), dtype="boolean"
        )
    elif "Active" in df.columns:
        result["intended_run"] = pd.Series(df.get("Active"), dtype="boolean")
    else:
        intended_run_flags = derive_weekly_intended_run_flags(data)
        result = result.merge(
            intended_run_flags,
            on=["iso_week", "campaign", "ad_name"],
            how="left",
        )
        result["intended_run"] = result["intended_run"].astype("boolean")

    return result


def generate_ad_run_summary(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate ad_run_summary table from Derived_Last_Run_Ad_Metrics.

    Grain: one row per ad × contiguous run (only last run currently available)
    """
    df = extract_table_df(data, "Derived_Last_Run_Ad_Metrics")

    if df.empty:
        return pd.DataFrame(
            columns=[
                "campaign",
                "ad_name",
                "run_start_week",
                "run_end_week",
                "weeks_in_run",
                "run_spend",
                "run_leads",
                "run_cpl",
            ]
        )

    result = pd.DataFrame(
        {
            "campaign": map_campaign_to_letter(
                df["Campaign"] if "Campaign" in df.columns else pd.Series(dtype=str)
            ),
            "ad_name": df["Ad"] if "Ad" in df.columns else pd.Series(dtype=str),
            "run_start_week": (
                df["Week_last_run_start"]
                if "Week_last_run_start" in df.columns
                else pd.Series(dtype=str)
            ),
            "run_end_week": (
                df["Week_last_run_end"]
                if "Week_last_run_end" in df.columns
                else pd.Series(dtype=str)
            ),
            "weeks_in_run": pd.to_numeric(
                (
                    df["Weeks_in_last_run"]
                    if "Weeks_in_last_run" in df.columns
                    else pd.Series(dtype=int)
                ),
                errors="coerce",
            ).astype("Int64"),
            "run_spend": pd.to_numeric(
                (
                    df["Spend_last_run"]
                    if "Spend_last_run" in df.columns
                    else pd.Series(dtype=float)
                ),
                errors="coerce",
            ),
            "run_leads": pd.to_numeric(
                (
                    df["Leads_last_run"]
                    if "Leads_last_run" in df.columns
                    else pd.Series(dtype=int)
                ),
                errors="coerce",
            ).astype("Int64"),
            "run_cpl": pd.to_numeric(
                (
                    df["CPL_last_run"]
                    if "CPL_last_run" in df.columns
                    else pd.Series(dtype=float)
                ),
                errors="coerce",
            ),
        }
    )

    return result


def generate_ad_lifetime_summary(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate ad_lifetime_summary table from Derived_Lifetime_Ad_Metrics.

    Grain: one row per ad
    """
    df = extract_table_df(data, "Derived_Lifetime_Ad_Metrics")

    if df.empty:
        return pd.DataFrame(
            columns=[
                "campaign",
                "ad_name",
                "lifetime_spend",
                "lifetime_leads",
                "lifetime_cpl",
                "first_seen_week",
                "last_seen_week",
                "weeks_active",
            ]
        )

    result = pd.DataFrame(
        {
            "campaign": map_campaign_to_letter(
                df["Campaign"] if "Campaign" in df.columns else pd.Series(dtype=str)
            ),
            "ad_name": df["Ad"] if "Ad" in df.columns else pd.Series(dtype=str),
            "lifetime_spend": pd.to_numeric(
                df["Spend"] if "Spend" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
            "lifetime_leads": pd.to_numeric(
                df["Leads"] if "Leads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "lifetime_cpl": pd.to_numeric(
                df["CPL"] if "CPL" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
            "first_seen_week": (
                df["FirstWeek"] if "FirstWeek" in df.columns else pd.Series(dtype=str)
            ),
            "last_seen_week": (
                df["LastWeek"] if "LastWeek" in df.columns else pd.Series(dtype=str)
            ),
            "weeks_active": pd.to_numeric(
                df["Weeks"] if "Weeks" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
        }
    )

    return result


def generate_ad_components(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate ad_components table by joining Ads → Creatives → Media/Headlines/Texts.

    Grain: one row per ad
    """
    ads_df = extract_table_df(data, "Ads")
    creatives_df = extract_table_df(data, "Creatives")
    media_df = extract_table_df(data, "Media")
    headlines_df = extract_table_df(data, "Headlines")
    texts_df = extract_table_df(data, "Texts")

    if ads_df.empty:
        return pd.DataFrame(
            columns=[
                "ad_id",
                "ad_name",
                "campaign",
                "media_id",
                "media_name",
                "headline_id",
                "headline_text",
                "text_id",
                "text_name",
            ]
        )

    # Preserve important columns by renaming before joins to avoid collisions
    ads_df = ads_df.rename(columns={"Text": "Text_ref", "Name": "ad_name"})

    # Normalize join key dtypes to avoid pandas merge errors when keys
    # are inferred as mixed types (e.g., object vs int64).
    for df_ in (ads_df, creatives_df, media_df, headlines_df, texts_df):
        for col in ("id", "Creative", "Media", "Headline", "Text", "Text_ref"):
            if col in df_.columns:
                df_[col] = df_[col].astype("string")

    # Join Ads → Creatives
    ads_with_creative = ads_df.merge(
        creatives_df[["id", "Media", "Headline"]],
        left_on="Creative",
        right_on="id",
        how="left",
        suffixes=("", "_creative"),
    )

    # Join → Media
    ads_with_media = ads_with_creative.merge(
        media_df[["id", "Name"]],
        left_on="Media",
        right_on="id",
        how="left",
        suffixes=("", "_media"),
    ).rename(columns={"Name": "media_name", "id_media": "media_id"})

    # Join → Headlines
    ads_with_headline = ads_with_media.merge(
        headlines_df[["id", "Text"]],
        left_on="Headline",
        right_on="id",
        how="left",
        suffixes=("", "_headline"),
    ).rename(columns={"Text": "headline_text", "id_headline": "headline_id"})

    # Join → Texts
    ads_with_text = ads_with_headline.merge(
        texts_df[["id", "Name"]],
        left_on="Text_ref",
        right_on="id",
        how="left",
        suffixes=("", "_text"),
    ).rename(columns={"Name": "text_name", "id_text": "text_id"})

    result = pd.DataFrame(
        {
            "ad_id": ads_with_text["id"],
            "ad_name": ads_with_text["ad_name"],
            "campaign": map_campaign_to_letter(
                ads_with_text["Campaign"]
                if "Campaign" in ads_with_text.columns
                else pd.Series(dtype=str)
            ),
            "media_id": (
                ads_with_text["media_id"]
                if "media_id" in ads_with_text.columns
                else pd.Series(dtype="Int64")
            ),
            "media_name": (
                ads_with_text["media_name"]
                if "media_name" in ads_with_text.columns
                else pd.Series(dtype=str)
            ),
            "headline_id": (
                ads_with_text["headline_id"]
                if "headline_id" in ads_with_text.columns
                else pd.Series(dtype="Int64")
            ),
            "headline_text": (
                ads_with_text["headline_text"]
                if "headline_text" in ads_with_text.columns
                else pd.Series(dtype=str)
            ),
            "text_id": (
                ads_with_text["text_id"]
                if "text_id" in ads_with_text.columns
                else pd.Series(dtype="Int64")
            ),
            "text_name": (
                ads_with_text["text_name"]
                if "text_name" in ads_with_text.columns
                else pd.Series(dtype=str)
            ),
        }
    )

    return result


def generate_component_tags(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate component_tags table from Derived_Component_Tags.

    Grain: one row per component × tag
    """
    df = extract_table_df(data, "Derived_Component_Tags")

    if df.empty:
        return pd.DataFrame(
            columns=[
                "component_type",
                "component_id",
                "component_name",
                "tag_type",
                "tag_value",
            ]
        )

    result = pd.DataFrame(
        {
            "component_type": (
                df["component_type"]
                if "component_type" in df.columns
                else pd.Series(dtype=str)
            ),
            "component_id": pd.to_numeric(
                (
                    df["component_id"]
                    if "component_id" in df.columns
                    else pd.Series(dtype=int)
                ),
                errors="coerce",
            ).astype("Int64"),
            "component_name": (
                df["component_name"]
                if "component_name" in df.columns
                else pd.Series(dtype=str)
            ),
            "tag_type": (
                df["tag_type"] if "tag_type" in df.columns else pd.Series(dtype=str)
            ),
            "tag_value": (
                df["tag_value"] if "tag_value" in df.columns else pd.Series(dtype=str)
            ),
        }
    )

    return result


def generate_component_media_lifetime(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate component_media_lifetime table from Derived_Component_Media_Lifetime.

    Grain: one row per media component
    """
    df = extract_table_df(data, "Derived_Component_Media_Lifetime")

    if df.empty:
        return pd.DataFrame(
            columns=[
                "media_id",
                "media_name",
                "media_variant",
                "media_format",
                "spend",
                "leads",
                "ads",
                "cpl",
            ]
        )

    result = pd.DataFrame(
        {
            "media_id": pd.to_numeric(
                df.get("Media_ID") if "Media_ID" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "media_name": (
                df.get("Name")
                if "Name" in df.columns
                else df.get("Media_Name", pd.Series(dtype=str))
            ),
            "media_variant": (
                df.get("Variant") if "Variant" in df.columns else pd.Series(dtype=str)
            ),
            "media_format": (
                df.get("Format") if "Format" in df.columns else pd.Series(dtype=str)
            ),
            "spend": pd.to_numeric(
                df.get("Spend") if "Spend" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
            "leads": pd.to_numeric(
                df.get("Leads") if "Leads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "ads": pd.to_numeric(
                df.get("Ads") if "Ads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "cpl": pd.to_numeric(
                df.get("CPL") if "CPL" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
        }
    )

    return result


def generate_component_headline_lifetime(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate component_headline_lifetime table from Derived_Component_Headline_Lifetime.

    Grain: one row per headline component
    """
    df = extract_table_df(data, "Derived_Component_Headline_Lifetime")

    if df.empty:
        return pd.DataFrame(
            columns=[
                "headline_id",
                "headline_text",
                "spend",
                "leads",
                "ads",
                "cpl",
            ]
        )

    result = pd.DataFrame(
        {
            "headline_id": pd.to_numeric(
                df.get("Headline_ID")
                if "Headline_ID" in df.columns
                else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "headline_text": (
                df.get("Headline_Text")
                if "Headline_Text" in df.columns
                else df.get("Text", pd.Series(dtype=str))
            ),
            "spend": pd.to_numeric(
                df.get("Spend") if "Spend" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
            "leads": pd.to_numeric(
                df.get("Leads") if "Leads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "ads": pd.to_numeric(
                df.get("Ads") if "Ads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "cpl": pd.to_numeric(
                df.get("CPL") if "CPL" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
        }
    )

    return result


def generate_component_text_lifetime(data: Dict[str, Any]) -> pd.DataFrame:
    """
    Generate component_text_lifetime table from Derived_Component_Text_Lifetime.

    Grain: one row per text component
    """
    df = extract_table_df(data, "Derived_Component_Text_Lifetime")

    if df.empty:
        return pd.DataFrame(
            columns=[
                "text_id",
                "text_name",
                "text_variant",
                "primary_text",
                "spend",
                "leads",
                "ads",
                "cpl",
            ]
        )

    result = pd.DataFrame(
        {
            "text_id": pd.to_numeric(
                df.get("Text_ID") if "Text_ID" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "text_name": (
                df.get("Name") if "Name" in df.columns else pd.Series(dtype=str)
            ),
            "text_variant": (
                df.get("Variant") if "Variant" in df.columns else pd.Series(dtype=str)
            ),
            "primary_text": (
                df.get("Primary_text")
                if "Primary_text" in df.columns
                else pd.Series(dtype=str)
            ),
            "spend": pd.to_numeric(
                df.get("Spend") if "Spend" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
            "leads": pd.to_numeric(
                df.get("Leads") if "Leads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "ads": pd.to_numeric(
                df.get("Ads") if "Ads" in df.columns else pd.Series(dtype=int),
                errors="coerce",
            ).astype("Int64"),
            "cpl": pd.to_numeric(
                df.get("CPL") if "CPL" in df.columns else pd.Series(dtype=float),
                errors="coerce",
            ),
        }
    )

    return result


def main(
    json_path: str = "outputs/performance_data.json",
    output_dir: str = "outputs",
    format: str = "csv",
):
    """
    Main entry point: convert performance_data.json to structured files.

    Args:
        json_path: Path to performance_data.json
        output_dir: Directory to save output files
        format: Output format - 'csv', 'parquet', or 'both' (default: 'csv')
    """
    print(f"Loading performance data from {json_path}...")
    data = load_performance_data(json_path)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("\n📊 Generating structured tables...")

    # Generate each table
    tables = {
        "ad_weekly_performance": generate_ad_weekly_performance(data),
        "ad_run_summary": generate_ad_run_summary(data),
        "ad_lifetime_summary": generate_ad_lifetime_summary(data),
        "ad_components": generate_ad_components(data),
        "component_media_lifetime": generate_component_media_lifetime(data),
        "component_headline_lifetime": generate_component_headline_lifetime(data),
        "component_text_lifetime": generate_component_text_lifetime(data),
        "component_tags": generate_component_tags(data),
    }

    # Save files in requested format(s)
    for name, df in tables.items():
        if format in ["csv", "both"]:
            csv_path = output_path / f"{name}.csv"
            df.to_csv(csv_path, index=False)
            print(f"  ✓ {name}: {len(df)} rows → {csv_path}")

        if format in ["parquet", "both"]:
            parquet_path = output_path / f"{name}.parquet"
            df.to_parquet(parquet_path, index=False, engine="pyarrow")
            print(f"  ✓ {name}: {len(df)} rows → {parquet_path}")

    print(f"\n✅ Structured export complete! Files saved to {output_dir}/")
    return tables


if __name__ == "__main__":
    import sys

    # Allow optional command-line arguments
    json_path = sys.argv[1] if len(sys.argv) > 1 else "outputs/performance_data.json"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
    format = sys.argv[3] if len(sys.argv) > 3 else "csv"

    main(json_path, output_dir, format)

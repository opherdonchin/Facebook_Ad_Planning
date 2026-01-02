import argparse
import re
from pathlib import Path

import pandas as pd


# ----------------------------
# Helpers
# ----------------------------

def _is_blank(x: object) -> bool:
    return x is None or (isinstance(x, float) and pd.isna(x)) or str(x).strip() == ""


def _norm_phone(x: object) -> str:
    if _is_blank(x):
        return ""
    return re.sub(r"\D+", "", str(x))


def _norm_email(x: object) -> str:
    if _is_blank(x):
        return ""
    return str(x).strip().lower()


def _norm_name(x: object) -> str:
    if _is_blank(x):
        return ""
    return re.sub(r"\s+", " ", str(x).strip())


def _name_is_hebrew(name: str) -> bool:
    return bool(re.search(r"[\u0590-\u05FF]", name or ""))


def _parse_lead_dates(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s, errors="coerce")


def _parse_fb_times(s: pd.Series) -> pd.Series:
    t = pd.to_datetime(s, errors="coerce", utc=True)
    return t.dt.tz_convert(None)


def _squawk(msg: str) -> None:
    print(f"[SQUAWK] {msg}")


def _ensure_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    return df


# ----------------------------
# Core logic
# ----------------------------

def update_leads_sources(
    leads_df: pd.DataFrame,
    fb_df: pd.DataFrame,
    *,
    leads_date_col: str = "Date",
    leads_phone_col: str = "Phone",
    leads_email_col: str = "Email",
    name_he_col: str = "Name Hebrew",
    name_en_col: str = "Name English",
    src_campaign_col: str = "Source Campaign",
    src_ad_col: str = "Source Ad name",
    src_platform_col: str = "Source Platform",
    max_gap_days: int = 3,
) -> pd.DataFrame:

    # Ensure required columns exist
    leads_df = _ensure_columns(
        leads_df,
        [
            leads_email_col,
            name_he_col,
            name_en_col,
            src_campaign_col,
            src_ad_col,
            src_platform_col,
        ],
    ).copy()

    fb_df = fb_df.copy()

    # Parse dates
    leads_df["_lead_date"] = _parse_lead_dates(leads_df.get(leads_date_col))
    fb_df["_fb_time"] = _parse_fb_times(fb_df["created_time"])

    # Normalize keys
    leads_df["_phone"] = leads_df[leads_phone_col].map(_norm_phone)
    leads_df["_email"] = leads_df[leads_email_col].map(_norm_email)

    fb_df["_phone"] = fb_df["phone_number"].map(_norm_phone)
    fb_df["_email"] = fb_df["email"].map(_norm_email)
    fb_df["_name"] = fb_df["full_name"].map(_norm_name)

    # Build lookup: (phone, email) → list of lead indices
    lead_index = {}
    for idx, r in leads_df.iterrows():
        if r["_phone"] and r["_email"]:
            lead_index.setdefault((r["_phone"], r["_email"]), []).append(idx)

    def _pick_best(indices, fb_time):
        sub = leads_df.loc[indices]
        if pd.notna(fb_time) and sub["_lead_date"].notna().any():
            return int(((sub["_lead_date"] - fb_time).abs()).idxmin())
        return int(indices[0])

    created = updated = name_mismatches = gap_warnings = 0

    # Process FB rows
    for _, fb in fb_df.iterrows():
        fb_phone = fb["_phone"]
        fb_email = fb["_email"]
        fb_name = fb.get("full_name")
        fb_time = fb["_fb_time"]

        if not fb_phone or not fb_email:
            _squawk(
                f"FB row missing phone/email; skipped. "
                f"id={fb.get('id')}, phone={fb.get('phone_number')}, email={fb.get('email')}"
            )
            continue

        key = (fb_phone, fb_email)
        matches = lead_index.get(key, [])

        # ----------------------------
        # No match → create new lead
        # ----------------------------
        if not matches:
            new_row = {c: pd.NA for c in leads_df.columns}

            new_row[leads_phone_col] = fb.get("phone_number")
            new_row[leads_email_col] = fb.get("email")
            if pd.notna(fb_time):
                new_row[leads_date_col] = fb_time.date().isoformat()

            if fb_name:
                if _name_is_hebrew(fb_name):
                    new_row[name_he_col] = fb_name
                else:
                    new_row[name_en_col] = fb_name

            new_row[src_campaign_col] = fb.get("campaign_name")
            new_row[src_ad_col] = fb.get("ad_name")
            new_row[src_platform_col] = fb.get("platform")

            leads_df = pd.concat([leads_df, pd.DataFrame([new_row])], ignore_index=True)
            new_idx = int(leads_df.index[-1])
            lead_index.setdefault(key, []).append(new_idx)

            created += 1
            _squawk(
                f"CREATED new lead (no phone+email match). "
                f"phone={fb_phone}, email={fb_email}, name={fb_name}, "
                f"created_time={fb.get('created_time')}, "
                f"campaign={fb.get('campaign_name')}, ad={fb.get('ad_name')}, platform={fb.get('platform')}"
            )
            continue

        # ----------------------------
        # Matched lead
        # ----------------------------
        lead_idx = _pick_best(matches, fb_time)
        lead = leads_df.loc[lead_idx]

        # Name handling (never overwrite)
        fb_norm = _norm_name(fb_name)
        fb_is_he = _name_is_hebrew(fb_name) if fb_name else False

        lead_he = lead.get(name_he_col)
        lead_en = lead.get(name_en_col)
        lead_he_norm = _norm_name(lead_he)
        lead_en_norm = _norm_name(lead_en)

        if fb_norm:
            if fb_is_he:
                if _is_blank(lead_he):
                    leads_df.at[lead_idx, name_he_col] = fb_name
                elif fb_norm != lead_he_norm:
                    name_mismatches += 1
                    _squawk(
                        f"NAME MISMATCH (HE). lead_row={lead_idx}, "
                        f"phone={fb_phone}, email={fb_email}, "
                        f"LeadHE={lead_he}, LeadEN={lead_en}, FBName={fb_name}"
                    )
            else:
                if _is_blank(lead_en):
                    leads_df.at[lead_idx, name_en_col] = fb_name
                elif fb_norm != lead_en_norm:
                    name_mismatches += 1
                    _squawk(
                        f"NAME MISMATCH (EN). lead_row={lead_idx}, "
                        f"phone={fb_phone}, email={fb_email}, "
                        f"LeadHE={lead_he}, LeadEN={lead_en}, FBName={fb_name}"
                    )

        # Time gap check
        lead_date = lead["_lead_date"]
        if pd.notna(lead_date) and pd.notna(fb_time):
            gap = abs((lead_date - fb_time).days)
            if gap > max_gap_days:
                gap_warnings += 1
                _squawk(
                    f"TIME GAP > {max_gap_days} days. lead_row={lead_idx}, "
                    f"phone={fb_phone}, email={fb_email}, "
                    f"LeadDate={lead_date.date()}, FBTime={fb_time}, gap_days={gap}"
                )

        # Always update sources
        leads_df.at[lead_idx, src_campaign_col] = fb.get("campaign_name")
        leads_df.at[lead_idx, src_ad_col] = fb.get("ad_name")
        leads_df.at[lead_idx, src_platform_col] = fb.get("platform")
        updated += 1

    # Cleanup
    leads_df.drop(columns=["_lead_date", "_phone", "_email"], inplace=True, errors="ignore")

    print(f"Updated leads: {updated}")
    print(f"Created leads: {created}")
    print(f"Name mismatch squawks: {name_mismatches}")
    print(f"Time gap squawks: {gap_warnings}")

    return leads_df


#

# =========================
# file: grist_leads_source_sync.py
# =========================
import argparse
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from grist.grist import GristClient


# -------------------------
# Helpers: normalization
# -------------------------
_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
_EMAIL_RE = re.compile(r"^\s*[^@\s]+@[^@\s]+\.[^@\s]+\s*$", re.IGNORECASE)


def is_hebrew(s: str) -> bool:
    return bool(_HEBREW_RE.search(s or ""))


def norm_email(email: Optional[str]) -> str:
    if not email:
        return ""
    e = str(email).strip().lower()
    return e if _EMAIL_RE.match(e) else e  # we still keep it; validation is best-effort


def norm_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    p = str(phone).strip()
    original = p  # Keep original for warning message
    p = re.sub(r"[^\d+]", "", p)

    # Handle +972 country code
    if p.startswith("+972"):
        remaining = p[4:]  # Strip +972
        digit_count = len(remaining)

        if digit_count == 9 and remaining[0] == "5":
            # 9 digits starting with 5: add leading 0 → 0512345678
            return "0" + remaining
        elif digit_count == 10 and remaining[0] == "0":
            # 10 digits starting with 0: use as-is → 0512345678
            return remaining
        else:
            # Other cases: keep full number as it appears in form and warn
            print(f"[PHONE WARNING] Unusual +972 format: {original} -> keeping as-is")
            return original

    # Common Israeli cases without +972: "05xxxxxxxx" -> "9725xxxxxxxx"
    if p.startswith("+"):
        p = p[1:]
    if p.startswith("0") and len(p) >= 9:
        p = "972" + p[1:]
    return p


def parse_dt(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    s = str(s).strip()
    if not s:
        return None

    # Try various date formats
    formats = [
        # Facebook export ISO with timezone: 2025-12-26T10:13:34+02:00
        None,  # fromisoformat
        # Grist date columns: YYYY-MM-DD
        "%Y-%m-%d",
        # CSV export format: 01/01/2026 7:10am or 12/30/2025 9:44pm
        "%m/%d/%Y %I:%M%p",
        "%d/%m/%Y %I:%M%p",
    ]

    for fmt in formats:
        try:
            if fmt is None:
                dt = datetime.fromisoformat(s)
            else:
                dt = datetime.strptime(s, fmt)
            # Ensure timezone-aware datetime
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue

    return None


def dt_to_grist_date(d: datetime) -> str:
    # Keep it simple: write YYYY-MM-DD into a Date column
    return d.date().isoformat()


# -------------------------
# FB export parsing (utf-16 + tab)
# -------------------------
def read_fb_export(path: str) -> List[Dict[str, Any]]:
    # Facebook lead export: Try different encodings since format may vary
    import csv

    # Try different encoding/delimiter combinations
    # Note: Facebook exports are typically UTF-16 tab-delimited, try that first
    configs = [
        ("utf-16", "\t"),
        ("utf-16-le", "\t"),
        ("utf-8", ","),
        ("utf-8", "\t"),
        ("latin-1", ","),
        ("latin-1", "\t"),
    ]

    for encoding, delimiter in configs:
        try:
            rows: List[Dict[str, Any]] = []
            with open(path, "r", encoding=encoding, errors="strict") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                first_row = None
                for row in reader:
                    if first_row is None:
                        first_row = row
                    rows.append(row)

            # Validate that we actually parsed columns (not one giant column)
            if rows and len(rows[0]) > 1:
                print(
                    f"[INFO] Successfully read file with encoding={encoding}, delimiter={repr(delimiter)}"
                )
                print(f"[INFO] Found {len(rows)} rows with {len(rows[0])} columns")
                return rows
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            # If it's not an encoding error, it might be the right encoding but wrong delimiter
            # Try next combination
            continue
            continue
        except Exception as e:
            # If it's not an encoding error, it might be the right encoding but wrong delimiter
            # Try next combination
            continue

    # If we get here, none of the encodings worked
    raise SystemExit(
        f"Error: Could not read {path} with any supported encoding. "
        f"Tried: utf-16, utf-8, utf-16-le, latin-1 with tab and comma delimiters."
    )


# -------------------------
# Main sync logic
# -------------------------
def pick_first_nonempty(*vals: Optional[str]) -> str:
    for v in vals:
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


def build_index(
    grist_records: List[Dict[str, Any]],
    col_phone: str,
    col_email: str,
) -> Tuple[Dict[Tuple[str, str], Dict[str, Any]], List[str]]:
    idx: Dict[Tuple[str, str], Dict[str, Any]] = {}
    warnings: List[str] = []
    for rec in grist_records:
        fields = rec.get("fields", {}) or {}
        key = (norm_phone(fields.get(col_phone)), norm_email(fields.get(col_email)))
        if key == ("", ""):
            continue
        if key in idx:
            warnings.append(
                f"[DUPLICATE KEY] Multiple Grist rows share phone+email key={key}. "
                f"Keeping first id={idx[key].get('id')}, also saw id={rec.get('id')}."
            )
            continue
        idx[key] = rec
    return idx, warnings


def safe_get(fields: Dict[str, Any], col: str) -> str:
    v = fields.get(col)
    return "" if v is None else str(v).strip()


def compute_updates_for_match(
    *,
    grist_fields: Dict[str, Any],
    fb_name: str,
    fb_phone: str,
    fb_email: str,
    fb_campaign: str,
    fb_ad: str,
    fb_platform: str,
    fb_created: Optional[datetime],
    cols: Dict[str, str],
    max_gap_days: int,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Returns:
      - fields_to_update (only non-empty additions; no overwrites unless filling missing bilingual name)
      - squawks (messages to print)
    """
    squawks: List[str] = []
    upd: Dict[str, Any] = {}

    # Existing values
    existing_phone = safe_get(grist_fields, cols["phone"])
    existing_email = safe_get(grist_fields, cols["email"])
    existing_name_en = safe_get(grist_fields, cols["name_en"])
    existing_name_he = safe_get(grist_fields, cols["name_he"])
    existing_campaign = safe_get(grist_fields, cols["campaign"])
    existing_ad = safe_get(grist_fields, cols["ad_name"])
    existing_platform = safe_get(grist_fields, cols["platform"])
    existing_date = parse_dt(safe_get(grist_fields, cols["date"]))

    # Name mismatch logic (no overwrites)
    fb_is_he = is_hebrew(fb_name)
    fb_name = fb_name.strip()

    # If bilingual complement: fill missing field ONLY
    if fb_name:
        if fb_is_he and not existing_name_he:
            upd[cols["name_he"]] = fb_name
            if existing_name_en:
                squawks.append(
                    f"[NAME COMPLEMENT] Added Hebrew name='{fb_name}' (English already present '{existing_name_en}')."
                )
        elif (not fb_is_he) and not existing_name_en:
            upd[cols["name_en"]] = fb_name
            if existing_name_he:
                squawks.append(
                    f"[NAME COMPLEMENT] Added English name='{fb_name}' (Hebrew already present '{existing_name_he}')."
                )
        else:
            # Both present or relevant one present. Check mismatch if same script-field differs.
            if fb_is_he and existing_name_he and fb_name != existing_name_he:
                squawks.append(
                    f"[NAME MISMATCH] phone={fb_phone} email={fb_email} : "
                    f"Grist Hebrew='{existing_name_he}' vs FB Hebrew='{fb_name}'. (No overwrite.)"
                )
            if (not fb_is_he) and existing_name_en and fb_name != existing_name_en:
                squawks.append(
                    f"[NAME MISMATCH] phone={fb_phone} email={fb_email} : "
                    f"Grist English='{existing_name_en}' vs FB English='{fb_name}'. (No overwrite.)"
                )

    # Source columns: never overwrite; only fill if blank
    if fb_campaign and not existing_campaign:
        upd[cols["campaign"]] = fb_campaign
    elif fb_campaign and existing_campaign and fb_campaign != existing_campaign:
        squawks.append(
            f"[SOURCE MISMATCH] phone={fb_phone} email={fb_email} : "
            f"Campaign Grist='{existing_campaign}' vs FB='{fb_campaign}'. (No overwrite.)"
        )

    if fb_ad and not existing_ad:
        upd[cols["ad_name"]] = fb_ad
    elif fb_ad and existing_ad and fb_ad != existing_ad:
        squawks.append(
            f"[SOURCE MISMATCH] phone={fb_phone} email={fb_email} : "
            f"Ad name Grist='{existing_ad}' vs FB='{fb_ad}'. (No overwrite.)"
        )

    if fb_platform and not existing_platform:
        upd[cols["platform"]] = fb_platform
    elif fb_platform and existing_platform and fb_platform != existing_platform:
        squawks.append(
            f"[SOURCE MISMATCH] phone={fb_phone} email={fb_email} : "
            f"Platform Grist='{existing_platform}' vs FB='{fb_platform}'. (No overwrite.)"
        )

    # Time gap check (> max_gap_days) between FB created_time and Grist Date (if both exist)
    if fb_created and existing_date:
        # Ensure both are timezone-aware for comparison
        fb_aware = (
            fb_created if fb_created.tzinfo else fb_created.replace(tzinfo=timezone.utc)
        )
        existing_aware = (
            existing_date
            if existing_date.tzinfo
            else existing_date.replace(tzinfo=timezone.utc)
        )
        gap_days = abs((fb_aware - existing_aware).days)
        if gap_days > max_gap_days:
            squawks.append(
                f"[TIME GAP] phone={fb_phone} email={fb_email} : "
                f"FB created={fb_created.isoformat()} vs Grist date={existing_date.isoformat()} "
                f"(gap>{max_gap_days} days)."
            )

    # If Grist missing Date, consider filling from FB created_time (optional, safe fill)
    if fb_created and not safe_get(grist_fields, cols["date"]):
        upd[cols["date"]] = dt_to_grist_date(fb_created)

    # Ensure canonical phone/email fields (fill if missing)
    if fb_phone and not existing_phone:
        upd[cols["phone"]] = fb_phone
    if fb_email and not existing_email:
        upd[cols["email"]] = fb_email

    return upd, squawks


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Sync Facebook Lead export into a Grist Leads table (fill source columns; create missing leads)."
    )
    ap.add_argument(
        "--fb-export",
        required=True,
        help="Path to Facebook lead export CSV/TSV (UTF-16 tab-delimited).",
    )
    ap.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json (same as export_ads.py).",
    )
    ap.add_argument(
        "--table",
        default=None,
        help="Grist tableId for leads (overrides config['leads_table_id']).",
    )
    ap.add_argument(
        "--max-gap-days",
        type=int,
        default=3,
        help="Squawk if FB created_time vs Grist date differs by more than this.",
    )
    args = ap.parse_args()

    # Load configuration
    from utils import load_config

    try:
        cfg = load_config(args.config)
    except FileNotFoundError as e:
        raise SystemExit(e)

    # Read from leads section
    leads_config = cfg.get("leads", {})
    doc_id = leads_config.get("doc_id")
    api_key = leads_config.get("api_key")
    server = leads_config.get("server", "https://docs.getgrist.com")
    table_id = args.table or leads_config.get("table_id") or "Leads"

    if not doc_id or not api_key:
        raise SystemExit(
            "Error: config.json must include leads.doc_id and leads.api_key."
        )

    # Column mapping (override via config['leads']['columns'])
    cols = {
        "phone": "Phone",
        "email": "Email",
        "name_en": "Name (EN)",
        "name_he": "Name (HE)",
        "date": "Date",
        "campaign": "Campaign",
        "ad_name": "Ad name",
        "platform": "Platform",
    }
    cols.update(leads_config.get("columns", {}) or {})

    # Validate all required columns are present
    required_cols = [
        "phone",
        "email",
        "name_en",
        "name_he",
        "date",
        "campaign",
        "ad_name",
        "platform",
    ]
    missing_cols = [col for col in required_cols if col not in cols]
    if missing_cols:
        raise SystemExit(
            f"Error: Missing required column mappings in config: {missing_cols}. "
            f"Ensure all required columns are defined in config['leads_columns'] or use defaults."
        )

    client = GristClient(server=server, doc_id=doc_id, api_key=api_key)

    # Pull current Grist leads
    grist_records = client.fetch_records(table_id)
    idx, idx_warnings = build_index(grist_records, cols["phone"], cols["email"])
    for w in idx_warnings:
        print(w)

    # Read FB export
    fb_rows = read_fb_export(args.fb_export)

    # Prepare batches
    patch_batch: List[Dict[str, Any]] = []
    add_batch: List[Dict[str, Any]] = []

    # For more informative squawks
    now = datetime.now(timezone.utc)

    for row in fb_rows:
        # Handle different CSV formats - try Facebook export columns first, then generic columns
        fb_email = norm_email(row.get("email") or row.get("Email"))
        fb_phone = norm_phone(
            row.get("phone_number")
            or row.get("phone")
            or row.get("Phone")
            or row.get("WhatsApp number")
        )
        fb_name = pick_first_nonempty(
            row.get("full_name"), row.get("name"), row.get("Name")
        )
        fb_campaign = pick_first_nonempty(
            row.get("campaign_name"),
            row.get("campaign"),
            row.get("Campaign"),
            row.get("Source"),
        )
        fb_ad = pick_first_nonempty(row.get("ad_name"), row.get("ad"), row.get("Form"))
        fb_platform = pick_first_nonempty(
            row.get("platform"), row.get("Platform"), row.get("Channel")
        )
        fb_created = parse_dt(row.get("created_time") or row.get("Created"))

        key = (fb_phone, fb_email)

        # Require BOTH phone and email for matching (per your rule)
        has_key = fb_phone != "" and fb_email != ""

        if not has_key:
            print(
                f"[SKIP] FB row missing phone and/or email; cannot match/create safely. "
                f"name='{fb_name}' phone='{fb_phone}' email='{fb_email}'"
            )
            continue

        existing = idx.get(key)

        if existing is None:
            # Create new record
            fields: Dict[str, Any] = {}

            # Put name in correct language column (and do not guess the other)
            if fb_name:
                if is_hebrew(fb_name):
                    fields[cols["name_he"]] = fb_name.strip()
                else:
                    fields[cols["name_en"]] = fb_name.strip()

            fields[cols["phone"]] = fb_phone
            fields[cols["email"]] = fb_email

            # Source fields
            if fb_campaign:
                fields[cols["campaign"]] = fb_campaign
            if fb_ad:
                fields[cols["ad_name"]] = fb_ad
            if fb_platform:
                fields[cols["platform"]] = fb_platform

            # Date: default to FB created_time date if available
            if fb_created:
                fields[cols["date"]] = dt_to_grist_date(fb_created)

                # Optional: also squawk if the lead is "old" relative to now by > max-gap-days
                fb_aware = (
                    fb_created
                    if fb_created.tzinfo
                    else fb_created.replace(tzinfo=timezone.utc)
                )
                gap_days = abs((now - fb_aware).days)
                if gap_days > args.max_gap_days:
                    print(
                        f"[TIME GAP] Creating lead but FB created_time is >{args.max_gap_days} days from now: "
                        f"created={fb_created.isoformat()} name='{fb_name}' phone={fb_phone} email={fb_email}"
                    )

            add_batch.append({"fields": fields})

            print(
                f"[NEW LEAD] Created new lead (no phone+email match). "
                f"name='{fb_name}' phone={fb_phone} email={fb_email} "
                f"campaign='{fb_campaign}' ad='{fb_ad}' platform='{fb_platform}'"
            )
            continue

        # Matched lead: update only missing fields; squawk on mismatches
        rec_id = existing.get("id")
        gr_fields = existing.get("fields", {}) or {}

        upd, squawks = compute_updates_for_match(
            grist_fields=gr_fields,
            fb_name=fb_name,
            fb_phone=fb_phone,
            fb_email=fb_email,
            fb_campaign=fb_campaign,
            fb_ad=fb_ad,
            fb_platform=fb_platform,
            fb_created=fb_created,
            cols=cols,
            max_gap_days=args.max_gap_days,
        )

        for s in squawks:
            print(s)

        if upd:
            patch_batch.append({"id": rec_id, "fields": upd})

    # Write back (PATCH + POST)
    if add_batch:
        ids = client.add_records(table_id, add_batch)
        print(f"[DONE] Added {len(ids)} new leads.")
    else:
        print("[DONE] Added 0 new leads.")

    if patch_batch:
        # Group records by their field keys (Grist requires same fields in a batch)
        from collections import defaultdict

        grouped = defaultdict(list)
        for rec in patch_batch:
            field_keys = tuple(sorted(rec["fields"].keys()))
            grouped[field_keys].append(rec)

        # Patch each group separately
        total_updated = 0
        for field_keys, records in grouped.items():
            CHUNK = 200
            for i in range(0, len(records), CHUNK):
                client.patch_records(table_id, records[i : i + CHUNK])
            total_updated += len(records)

        print(f"[DONE] Updated {total_updated} existing leads.")
    else:
        print("[DONE] Updated 0 existing leads.")


if __name__ == "__main__":
    main()

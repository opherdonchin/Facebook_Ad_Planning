# =========================
# file: grist_leads_source_sync.py
# =========================
import argparse
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests


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
    p = re.sub(r"[^\d+]", "", p)
    # Common Israeli cases: "05xxxxxxxx" -> "9725xxxxxxxx" ; "+9725xxxxxxx" -> "9725xxxxxxx"
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
    # Facebook export uses ISO with timezone: 2025-12-26T10:13:34+02:00
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    # Grist date columns might be YYYY-MM-DD
    try:
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def dt_to_grist_date(d: datetime) -> str:
    # Keep it simple: write YYYY-MM-DD into a Date column
    return d.date().isoformat()


# -------------------------
# Grist API client
# -------------------------
class GristClient:
    def __init__(self, server: str, doc_id: str, api_key: str) -> None:
        self.server = server.rstrip("/")
        self.doc_id = doc_id
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def _url(self, path: str) -> str:
        return f"{self.server}/api{path}"

    def fetch_records(self, table_id: str) -> List[Dict[str, Any]]:
        url = self._url(f"/docs/{self.doc_id}/tables/{table_id}/records")
        r = self.session.get(url, timeout=60)
        r.raise_for_status()
        return r.json().get("records", [])

    def add_records(self, table_id: str, records: List[Dict[str, Any]]) -> List[int]:
        url = self._url(f"/docs/{self.doc_id}/tables/{table_id}/records")
        payload = {"records": records}
        r = self.session.post(url, json=payload, timeout=60)
        r.raise_for_status()
        out = r.json().get("records", [])
        return [x.get("id") for x in out if "id" in x]

    def patch_records(self, table_id: str, records: List[Dict[str, Any]]) -> None:
        url = self._url(f"/docs/{self.doc_id}/tables/{table_id}/records")
        payload = {"records": records}
        r = self.session.patch(url, json=payload, timeout=60)
        r.raise_for_status()


# -------------------------
# FB export parsing (utf-16 + tab)
# -------------------------
def read_fb_export(path: str) -> List[Dict[str, Any]]:
    # Facebook lead export: UTF-16 with tab separators (as in your sample file)
    import csv

    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-16") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            rows.append(row)
    return rows


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
        gap = abs((fb_created - existing_date).total_seconds())
        if gap > max_gap_days * 86400:
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
    ap.add_argument("--fb-export", required=True, help="Path to Facebook lead export CSV/TSV (UTF-16 tab-delimited).")
    ap.add_argument("--config", default="config.json", help="Path to config.json (same as grist_export.py).")
    ap.add_argument("--table", default=None, help="Grist tableId for leads (overrides config['leads_table_id']).")
    ap.add_argument("--max-gap-days", type=int, default=3, help="Squawk if FB created_time vs Grist date differs by more than this.")
    args = ap.parse_args()

    if not os.path.exists(args.config):
        raise SystemExit(
            f"Error: {args.config} not found. Copy config.example.json -> config.json and add credentials."
        )

    with open(args.config, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    doc_id = cfg.get("doc_id")
    api_key = cfg.get("api_key")
    server = cfg.get("server", "https://docs.getgrist.com")
    table_id = args.table or cfg.get("leads_table_id") or "Leads"

    if not doc_id or not api_key:
        raise SystemExit("Error: config.json must include doc_id and api_key.")

    # Column mapping (override via config['leads_columns'])
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
    cols.update(cfg.get("leads_columns", {}) or {})

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
        fb_email = norm_email(row.get("email"))
        fb_phone = norm_phone(row.get("phone_number") or row.get("phone") or row.get("Phone"))
        fb_name = pick_first_nonempty(row.get("full_name"), row.get("name"))
        fb_campaign = pick_first_nonempty(row.get("campaign_name"), row.get("campaign"))
        fb_ad = pick_first_nonempty(row.get("ad_name"), row.get("ad"))
        fb_platform = pick_first_nonempty(row.get("platform"))
        fb_created = parse_dt(row.get("created_time"))

        key = (fb_phone, fb_email)

        # Require BOTH phone and email for matching (per your rule)
        has_key = (fb_phone != "" and fb_email != "")

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
                if abs((now - fb_created.astimezone(timezone.utc)).total_seconds()) > args.max_gap_days * 86400:
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
        # Patch in reasonable chunks (avoid huge requests)
        CHUNK = 200
        for i in range(0, len(patch_batch), CHUNK):
            client.patch_records(table_id, patch_batch[i : i + CHUNK])
        print(f"[DONE] Updated {len(patch_batch)} existing leads.")
    else:
        print("[DONE] Updated 0 existing leads.")


if __name__ == "__main__":
    main()



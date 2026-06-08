# =========================
# file: grist_leads_source.py
# =========================
import argparse
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from grist.grist import GristClient
from lead_utils import (
    build_index,
    compute_updates_for_match,
    dt_to_grist_date,
    format_squawk,
    is_hebrew,
    norm_email,
    norm_phone,
    parse_dt,
    pick_first_nonempty,
    safe_get,
)


# -------------------------
# FB export parsing (utf-16 + tab)
# -------------------------
def read_fb_export(path: str) -> List[Dict[str, Any]]:
    import csv

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
                for row in reader:
                    rows.append(row)

            if rows and len(rows[0]) > 1:
                print(
                    f"[INFO] Successfully read file with encoding={encoding}, delimiter={repr(delimiter)}"
                )
                print(f"[INFO] Found {len(rows)} rows with {len(rows[0])} columns")
                return rows
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            continue

    raise SystemExit(
        f"Error: Could not read {path} with any supported encoding. "
        f"Tried: utf-16, utf-8, utf-16-le, latin-1 with tab and comma delimiters."
    )


# -------------------------
# Main sync logic
# -------------------------
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
        help="Path to config.json.",
    )
    ap.add_argument(
        "--table",
        default=None,
        help="Grist tableId for leads (overrides config leads_table_id).",
    )
    ap.add_argument(
        "--max-gap-days",
        type=int,
        default=3,
        help="Squawk if FB created_time vs Grist date differs by more than this.",
    )
    ap.add_argument(
        "--verbose-pii",
        action="store_true",
        help="Print full phone/email in warnings (default: redacted).",
    )
    args = ap.parse_args()

    from utils import load_config

    try:
        cfg = load_config(args.config)
    except FileNotFoundError as e:
        raise SystemExit(e)

    leads_config = cfg.get("leads", {})
    doc_id = leads_config.get("doc_id")
    api_key = leads_config.get("api_key")
    server = leads_config.get("server", "https://docs.getgrist.com")
    table_id = args.table or leads_config.get("table_id") or "Leads"

    if not doc_id or not api_key:
        raise SystemExit(
            "Error: config.json must include leads.doc_id and leads.api_key."
        )

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

    required_cols = ["phone", "email", "name_en", "name_he", "date", "campaign", "ad_name", "platform"]
    missing_cols = [col for col in required_cols if col not in cols]
    if missing_cols:
        raise SystemExit(
            f"Error: Missing required column mappings in config: {missing_cols}."
        )

    client = GristClient(server=server, doc_id=doc_id, api_key=api_key)

    grist_records = client.fetch_records(table_id)
    idx, idx_warnings = build_index(grist_records, cols["phone"], cols["email"])
    for w in idx_warnings:
        print(format_squawk(w, verbose_pii=args.verbose_pii))

    fb_rows = read_fb_export(args.fb_export)

    patch_batch: List[Dict[str, Any]] = []
    add_batch: List[Dict[str, Any]] = []

    now = datetime.now(timezone.utc)

    for row in fb_rows:
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
        has_key = fb_phone != "" and fb_email != ""

        if not has_key:
            reason = []
            if not fb_phone:
                reason.append("missing phone")
            if not fb_email:
                reason.append("missing email")
            print(format_squawk({
                "type": "PARTIAL_CONTACT_SKIPPED",
                "phone": fb_phone,
                "email": fb_email,
                "detail": {"reason": " and ".join(reason), "meta_lead_id": ""},
            }, verbose_pii=args.verbose_pii))
            continue

        existing = idx.get(key)

        if existing is None:
            fields: Dict[str, Any] = {}

            if fb_name:
                if is_hebrew(fb_name):
                    fields[cols["name_he"]] = fb_name.strip()
                else:
                    fields[cols["name_en"]] = fb_name.strip()

            fields[cols["phone"]] = fb_phone
            fields[cols["email"]] = fb_email

            if fb_campaign:
                fields[cols["campaign"]] = fb_campaign
            if fb_ad:
                fields[cols["ad_name"]] = fb_ad
            if fb_platform:
                fields[cols["platform"]] = fb_platform

            if fb_created:
                fields[cols["date"]] = dt_to_grist_date(fb_created)

                fb_aware = (
                    fb_created if fb_created.tzinfo else fb_created.replace(tzinfo=timezone.utc)
                )
                gap_days = abs((now - fb_aware).days)
                if gap_days > args.max_gap_days:
                    print(
                        f"[TIME GAP] Creating lead but FB created_time is >{args.max_gap_days} days "
                        f"from now: created={fb_created.isoformat()} name='{fb_name}'"
                    )

            add_batch.append({"fields": fields})
            print(
                f"[NEW LEAD] Created new lead. "
                f"name='{fb_name}' campaign='{fb_campaign}' ad='{fb_ad}'"
            )
            continue

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

        for w in squawks:
            print(format_squawk(w, verbose_pii=args.verbose_pii))

        if upd:
            patch_batch.append({"id": rec_id, "fields": upd})

    if add_batch:
        ids = client.add_records(table_id, add_batch)
        print(f"[DONE] Added {len(ids)} new leads.")
    else:
        print("[DONE] Added 0 new leads.")

    if patch_batch:
        from collections import defaultdict

        grouped = defaultdict(list)
        for rec in patch_batch:
            field_keys = tuple(sorted(rec["fields"].keys()))
            grouped[field_keys].append(rec)

        total_updated = 0
        for field_keys, records in grouped.items():
            CHUNK = 200
            for i in range(0, len(records), CHUNK):
                client.patch_records(table_id, records[i: i + CHUNK])
            total_updated += len(records)

        print(f"[DONE] Updated {total_updated} existing leads.")
    else:
        print("[DONE] Updated 0 existing leads.")


if __name__ == "__main__":
    main()

"""Sync Meta (Facebook) Lead Ads into Grist via the Graph API.

Usage:
    pixi run sync_meta_leads
    python src/sync_meta_leads.py --dry-run
    python src/sync_meta_leads.py --lookback-days 30
    python src/sync_meta_leads.py --since 2026-06-01
    python src/sync_meta_leads.py --form-id 23944636508501947
    python src/sync_meta_leads.py --config config.json --dry-run --verbose-pii
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from grist.grist import GristClient
from lead_utils import (
    build_core_lead_fields,
    build_index,
    compute_updates_for_match,
    flush_batches,
    format_squawk,
    norm_email,
    norm_phone,
    parse_dt,
    safe_get,
)
from meta_leads import MetaLeadsClient, parse_meta_lead
from utils import load_config


# ---------------------------------------------------------------------------
# Ad name resolution
# ---------------------------------------------------------------------------
def resolve_ad_name(lead: Dict[str, Any], ad_id_map: Dict[str, str]) -> str:
    """Return ad_name from API response, or fall back to config mapping."""
    if lead.get("ad_name"):
        return lead["ad_name"]
    return ad_id_map.get(lead.get("ad_id", ""), "")


# ---------------------------------------------------------------------------
# Grist meta-ID index
# ---------------------------------------------------------------------------
def build_meta_id_index(
    grist_records: List[Dict[str, Any]],
    col_meta_lead_id: str,
) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """Build meta_lead_id → grist_record index.

    Returns (index, warnings) where warnings are structured dicts.
    """
    idx: Dict[str, Dict[str, Any]] = {}
    warnings: List[Dict[str, Any]] = []
    if not col_meta_lead_id:
        return idx, warnings

    for rec in grist_records:
        fields = rec.get("fields", {}) or {}
        mid = str(fields.get(col_meta_lead_id) or "").strip()
        if not mid:
            continue
        if mid in idx:
            warnings.append({
                "type": "DUPLICATE_META_ID_IN_GRIST",
                "phone": "",
                "email": "",
                "detail": {
                    "meta_lead_id": mid,
                    "kept_id": idx[mid].get("id"),
                    "also_saw_id": rec.get("id"),
                },
            })
            continue
        idx[mid] = rec

    return idx, warnings


# ---------------------------------------------------------------------------
# Column validation
# ---------------------------------------------------------------------------
_REQUIRED_COL_KEYS = ["phone", "email", "name_en", "name_he", "date", "campaign", "ad_name", "platform"]

_INACTIVE_STATUSES = frozenset({"Failed", "Pause", "Registered"})


def validate_required_cols(
    cols: Dict[str, str],
    allow_no_meta_id: bool = False,
    dry_run: bool = False,
) -> None:
    """Raise SystemExit with a clear message if required column mappings are missing."""
    missing = [k for k in _REQUIRED_COL_KEYS if not cols.get(k)]
    if missing:
        raise SystemExit(
            f"[CONFIG ERROR] Missing required Grist column mappings: {missing}.\n"
            f"Add them under leads.columns in your config.json."
        )

    if not cols.get("meta_lead_id"):
        if dry_run:
            print(
                "[WARNING] meta_lead_id column is not configured. "
                "Dry-run will use phone+email-only matching. "
                "Configure meta_lead_id in leads.columns before production use."
            )
        elif allow_no_meta_id:
            print(
                "[WARNING] meta_lead_id column is not configured (--allow-no-meta-id set). "
                "Idempotency relies on phone+email only."
            )
        else:
            raise SystemExit(
                "[CONFIG ERROR] meta_lead_id column is not configured.\n"
                "Add 'meta_lead_id': '<your Grist column ID>' under leads.columns in config.json.\n"
                "This column is required for idempotent production sync.\n"
                "Use --dry-run to test without this column, or --allow-no-meta-id to bypass (not recommended)."
            )


# ---------------------------------------------------------------------------
# Per-record update computation
# ---------------------------------------------------------------------------
def compute_meta_updates(
    *,
    grist_fields: Dict[str, Any],
    lead: Dict[str, Any],
    cols: Dict[str, str],
    canonical_json: str,
    verbose_pii: bool,
    max_gap_days: int,
    ad_id_map: Dict[str, str],
    now_iso: str,
) -> Tuple[Dict[str, Any], List[str]]:
    """Compute field updates for a matched Grist record.

    Calls compute_updates_for_match for CRM fields (conservative),
    then adds Meta-specific fill-if-missing and fill-or-update-if-changed logic.

    Returns (fields_to_update, formatted_warning_strings).
    """
    # CRM fields (conservative: fill-if-missing only, no overwrites)
    upd, raw_squawks = compute_updates_for_match(
        grist_fields=grist_fields,
        fb_name=lead.get("full_name", ""),
        fb_phone=lead.get("phone_number", ""),
        fb_email=lead.get("email", ""),
        fb_campaign=lead.get("campaign_name", ""),
        fb_ad=resolve_ad_name(lead, ad_id_map),
        fb_platform="Facebook",
        fb_created=lead.get("created_time"),
        cols=cols,
        max_gap_days=max_gap_days,
    )
    formatted_squawks = [format_squawk(w, verbose_pii=verbose_pii) for w in raw_squawks]

    # Meta attribution fields: fill-if-missing
    meta_fill_map = [
        ("meta_lead_id", lead.get("meta_lead_id", "")),
        ("meta_ad_id", lead.get("ad_id", "")),
        ("meta_campaign_id", lead.get("campaign_id", "")),
        ("meta_form_id", lead.get("form_id", "")),
    ]
    for col_key, value in meta_fill_map:
        col_name = cols.get(col_key, "")
        if col_name and value and not safe_get(grist_fields, col_name):
            upd[col_name] = value

    # meta_created_time: fill-if-missing
    col_ct = cols.get("meta_created_time", "")
    if col_ct and lead.get("created_time") and not safe_get(grist_fields, col_ct):
        upd[col_ct] = lead["created_time"].isoformat()

    # meta_raw_json: fill-if-missing or update if canonically changed
    col_json = cols.get("meta_raw_json", "")
    if col_json:
        existing_json_str = safe_get(grist_fields, col_json)
        if not existing_json_str:
            upd[col_json] = canonical_json
        else:
            try:
                existing_parsed = json.loads(existing_json_str)
            except (json.JSONDecodeError, ValueError):
                existing_parsed = None  # invalid stored JSON; replace it
            if existing_parsed != json.loads(canonical_json):
                upd[col_json] = canonical_json

    # imported_at: fill-if-missing only (never updated after first import)
    col_ia = cols.get("imported_at", "")
    if col_ia and not safe_get(grist_fields, col_ia):
        upd[col_ia] = now_iso

    # Reactivation: if lead re-submits while status is inactive, flip to Reactivated.
    # Guard: only reactivate for genuinely new submissions. If the Grist row already
    # stores this exact meta_lead_id, the lead is being re-read within the lookback
    # window — not a new form submission — so leave the status alone.
    col_status = cols.get("status", "")
    col_phone_notes = cols.get("phone_notes", "")
    col_mid = cols.get("meta_lead_id", "")
    stored_mid = safe_get(grist_fields, col_mid) if col_mid else ""
    is_new_submission = not stored_mid or stored_mid != lead.get("meta_lead_id", "")
    if col_status and is_new_submission:
        existing_status = safe_get(grist_fields, col_status)
        if existing_status in _INACTIVE_STATUSES:
            upd[col_status] = "Reactivated"
            if col_phone_notes:
                date_str = (
                    lead["created_time"].strftime("%Y-%m-%d")
                    if lead.get("created_time")
                    else now_iso[:10]
                )
                campaign = lead.get("campaign_name", "")
                ad = resolve_ad_name(lead, ad_id_map)
                note_parts = [f"Reactivated {date_str} via Meta lead"]
                if campaign:
                    note_parts.append(f"campaign: {campaign}")
                if ad:
                    note_parts.append(f"ad: {ad}")
                new_note = " — ".join(note_parts)
                existing_notes = safe_get(grist_fields, col_phone_notes)
                upd[col_phone_notes] = (
                    f"{existing_notes}\n{new_note}".strip() if existing_notes else new_note
                )
            formatted_squawks.append(format_squawk({
                "type": "REACTIVATED",
                "phone": lead.get("phone_number", ""),
                "email": lead.get("email", ""),
                "detail": {
                    "old_status": existing_status,
                    "meta_lead_id": lead.get("meta_lead_id", ""),
                },
            }, verbose_pii=verbose_pii))

    return upd, formatted_squawks


# ---------------------------------------------------------------------------
# New lead record builder
# ---------------------------------------------------------------------------
def build_new_lead_fields(
    *,
    lead: Dict[str, Any],
    cols: Dict[str, str],
    canonical_json: str,
    ad_id_map: Dict[str, str],
    now_iso: str,
) -> Dict[str, Any]:
    """Build the fields dict for a brand-new Grist lead record."""
    fields = build_core_lead_fields(
        cols=cols,
        name=lead.get("full_name", ""),
        phone=lead["phone_number"],
        email=lead["email"],
        campaign=lead.get("campaign_name", ""),
        ad_name=resolve_ad_name(lead, ad_id_map),
        platform="Facebook",
        created=lead.get("created_time"),
    )

    # Meta-specific fields (not present in CSV path)
    _set_if_col(fields, cols, "meta_lead_id", lead.get("meta_lead_id", ""))
    _set_if_col(fields, cols, "meta_ad_id", lead.get("ad_id", ""))
    _set_if_col(fields, cols, "meta_campaign_id", lead.get("campaign_id", ""))
    _set_if_col(fields, cols, "meta_form_id", lead.get("form_id", ""))

    col_ct = cols.get("meta_created_time", "")
    if col_ct and lead.get("created_time"):
        fields[col_ct] = lead["created_time"].isoformat()

    if cols.get("meta_raw_json"):
        fields[cols["meta_raw_json"]] = canonical_json

    if cols.get("imported_at"):
        fields[cols["imported_at"]] = now_iso

    return fields


def _set_if_col(fields: Dict[str, Any], cols: Dict[str, str], key: str, value: str) -> None:
    col_name = cols.get(key, "")
    if col_name and value:
        fields[col_name] = value


# ---------------------------------------------------------------------------
# Core sync function
# ---------------------------------------------------------------------------
def sync_meta_leads_to_grist(
    *,
    meta_client: MetaLeadsClient,
    grist_client: GristClient,
    form_ids: List[str],
    table_id: str,
    cols: Dict[str, str],
    ad_id_map: Dict[str, str],
    lookback_days: int = 14,
    since: Optional[datetime] = None,
    dry_run: bool = False,
    verbose_pii: bool = False,
    max_gap_days: int = 3,
    allow_no_meta_id: bool = False,
) -> Dict[str, int]:
    """Idempotent sync of Meta leads into Grist.

    Returns stats: forms_checked, leads_fetched, leads_skipped, leads_created,
    leads_updated, leads_already_current, warnings, errors.
    """
    # Validation
    validate_required_cols(cols, allow_no_meta_id=allow_no_meta_id, dry_run=dry_run)

    stats: Dict[str, int] = {
        "forms_checked": 0,
        "leads_fetched": 0,
        "leads_skipped": 0,
        "leads_created": 0,
        "leads_updated": 0,
        "leads_already_current": 0,
        "warnings": 0,
        "errors": 0,
    }

    now_iso = datetime.now(timezone.utc).isoformat()

    # Fetch and index existing Grist records
    print("[INFO] Fetching existing Grist leads...")
    grist_records = grist_client.fetch_records(table_id)
    print(f"[INFO] Found {len(grist_records)} existing Grist leads.")

    meta_id_idx, meta_idx_warnings = build_meta_id_index(grist_records, cols.get("meta_lead_id", ""))
    for w in meta_idx_warnings:
        print(format_squawk(w, verbose_pii=verbose_pii))
        stats["warnings"] += 1

    phone_email_idx, pe_warnings = build_index(grist_records, cols["phone"], cols["email"])
    for w in pe_warnings:
        print(format_squawk(w, verbose_pii=verbose_pii))
        stats["warnings"] += 1

    # In-run deduplication state
    seen_meta_ids: Set[str] = set()
    seen_phone_emails: Set[Tuple[str, str]] = set()

    add_batch: List[Dict[str, Any]] = []
    patch_batch: List[Dict[str, Any]] = []

    # Process each form
    for form_id in form_ids:
        stats["forms_checked"] += 1
        print(f"[INFO] Fetching leads for form {form_id} (lookback={lookback_days}d)...")

        try:
            raw_leads = meta_client.fetch_leads(
                form_id, lookback_days=lookback_days, since=since
            )
        except Exception as exc:
            print(f"[ERROR] Failed to fetch leads for form {form_id}: {exc}")
            stats["errors"] += 1
            continue

        print(f"[INFO] Fetched {len(raw_leads)} leads from form {form_id}.")
        stats["leads_fetched"] += len(raw_leads)

        for raw in raw_leads:
            try:
                lead = parse_meta_lead(raw)
            except Exception as exc:
                print(f"[ERROR] Failed to parse lead: {exc}. Raw id={raw.get('id', '?')}")
                stats["errors"] += 1
                continue

            mid = lead["meta_lead_id"]
            p = norm_phone(lead["phone_number"])
            e = norm_email(lead["email"])
            key: Tuple[str, str] = (p, e)
            has_full_contact = bool(p) and bool(e)

            canonical_json = json.dumps(lead["raw"], ensure_ascii=False, sort_keys=True)

            # --- Match / dedupe decision ---
            if mid and (mid in meta_id_idx or mid in seen_meta_ids):
                # Meta ID match
                if mid in meta_id_idx:
                    rec = meta_id_idx[mid]
                    rec_id = rec["id"]
                    gr_fields = rec.get("fields", {}) or {}
                    upd, squawks = compute_meta_updates(
                        grist_fields=gr_fields,
                        lead=lead,
                        cols=cols,
                        canonical_json=canonical_json,
                        verbose_pii=verbose_pii,
                        max_gap_days=max_gap_days,
                        ad_id_map=ad_id_map,
                        now_iso=now_iso,
                    )
                    for s in squawks:
                        print(s)
                        stats["warnings"] += 1
                    if upd:
                        patch_batch.append({"id": rec_id, "fields": upd})
                        stats["leads_updated"] += 1
                    else:
                        stats["leads_already_current"] += 1
                else:
                    # Already processed this run — in-run duplicate
                    print(format_squawk({
                        "type": "DUPLICATE_IN_RUN",
                        "phone": p,
                        "email": e,
                        "detail": {"meta_lead_id": mid},
                    }, verbose_pii=verbose_pii))
                seen_meta_ids.add(mid)
                if has_full_contact:
                    seen_phone_emails.add(key)

            elif has_full_contact and (key in phone_email_idx or key in seen_phone_emails):
                # Phone+email fallback match
                if key in phone_email_idx:
                    rec = phone_email_idx[key]
                    rec_id = rec["id"]
                    gr_fields = rec.get("fields", {}) or {}
                    upd, squawks = compute_meta_updates(
                        grist_fields=gr_fields,
                        lead=lead,
                        cols=cols,
                        canonical_json=canonical_json,
                        verbose_pii=verbose_pii,
                        max_gap_days=max_gap_days,
                        ad_id_map=ad_id_map,
                        now_iso=now_iso,
                    )
                    for s in squawks:
                        print(s)
                        stats["warnings"] += 1
                    if upd:
                        patch_batch.append({"id": rec_id, "fields": upd})
                        stats["leads_updated"] += 1
                    else:
                        stats["leads_already_current"] += 1
                else:
                    print(format_squawk({
                        "type": "DUPLICATE_IN_RUN",
                        "phone": p,
                        "email": e,
                        "detail": {"meta_lead_id": mid},
                    }, verbose_pii=verbose_pii))
                seen_phone_emails.add(key)
                if mid:
                    seen_meta_ids.add(mid)

            elif has_full_contact:
                # New lead
                fields = build_new_lead_fields(
                    lead=lead,
                    cols=cols,
                    canonical_json=canonical_json,
                    ad_id_map=ad_id_map,
                    now_iso=now_iso,
                )
                add_batch.append({"fields": fields})
                stats["leads_created"] += 1
                if mid:
                    seen_meta_ids.add(mid)
                seen_phone_emails.add(key)

            else:
                # Partial contact — skip
                reason = []
                if not p:
                    reason.append("missing phone")
                if not e:
                    reason.append("missing email")
                print(format_squawk({
                    "type": "PARTIAL_CONTACT_SKIPPED",
                    "phone": p,
                    "email": e,
                    "detail": {
                        "reason": " and ".join(reason),
                        "meta_lead_id": mid,
                    },
                }, verbose_pii=verbose_pii))
                stats["leads_skipped"] += 1

    # Write back
    if dry_run:
        print("\n[DRY RUN] No changes written to Grist.")
    else:
        n_added, n_patched = flush_batches(grist_client, table_id, add_batch, patch_batch)
        print(f"[DONE] Created {n_added} new leads.")
        print(f"[DONE] Updated {n_patched} existing leads.")

    return stats


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _print_summary(stats: Dict[str, int], dry_run: bool) -> None:
    prefix = "[DRY RUN] " if dry_run else ""
    print(f"\n{'='*50}")
    print(f"{prefix}Sync summary")
    print(f"{'='*50}")
    print(f"  Forms checked:       {stats['forms_checked']}")
    print(f"  Leads fetched:       {stats['leads_fetched']}")
    print(f"  Leads created:       {stats['leads_created']}")
    print(f"  Leads updated:       {stats['leads_updated']}")
    print(f"  Already current:     {stats['leads_already_current']}")
    print(f"  Leads skipped:       {stats['leads_skipped']}")
    print(f"  Warnings:            {stats['warnings']}")
    print(f"  Errors:              {stats['errors']}")
    print(f"{'='*50}\n")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Sync Meta Lead Ads into Grist via the Graph API."
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print proposed changes without writing to Grist.",
    )
    ap.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Fetch leads submitted within the last N days (default: from config or 14).",
    )
    ap.add_argument(
        "--since",
        default=None,
        metavar="YYYY-MM-DD",
        help="Fetch leads submitted on or after this date (overrides --lookback-days).",
    )
    ap.add_argument(
        "--form-id",
        action="append",
        dest="form_ids",
        metavar="FORM_ID",
        help="Meta lead form ID. Repeatable. Overrides config form_ids.",
    )
    ap.add_argument(
        "--config",
        default="config.json",
        help="Path to config.json (default: config.json).",
    )
    ap.add_argument(
        "--verbose-pii",
        action="store_true",
        help="Print full phone/email in logs (default: redacted).",
    )
    ap.add_argument(
        "--allow-no-meta-id",
        action="store_true",
        help="Allow sync without meta_lead_id column (idempotency relies on phone+email only).",
    )
    ap.add_argument(
        "--table",
        default=None,
        help="Grist table ID for leads (overrides config).",
    )
    args = ap.parse_args()

    try:
        cfg = load_config(args.config)
    except FileNotFoundError as exc:
        raise SystemExit(exc)

    leads_cfg = cfg.get("leads", {})
    meta_cfg = cfg.get("meta", {})

    # Grist connection
    doc_id = leads_cfg.get("doc_id", "")
    api_key = leads_cfg.get("api_key", "")
    server = leads_cfg.get("server", "https://docs.getgrist.com")
    table_id = args.table or leads_cfg.get("table_id", "Leads")

    if not doc_id or not api_key:
        raise SystemExit(
            "[CONFIG ERROR] config.json must include leads.doc_id and leads.api_key."
        )

    # Column mapping — start with defaults, overlay config, overlay Meta-specific keys
    cols: Dict[str, str] = {
        "phone": "Phone",
        "email": "Email",
        "name_en": "Name (EN)",
        "name_he": "Name (HE)",
        "date": "Date",
        "campaign": "Campaign",
        "ad_name": "Ad name",
        "platform": "Platform",
        "status": "Status",
        "phone_notes": "Phone_notes",
        # Meta columns default to "" (not configured)
        "meta_lead_id": "",
        "meta_created_time": "",
        "meta_ad_id": "",
        "meta_campaign_id": "",
        "meta_form_id": "",
        "meta_raw_json": "",
        "imported_at": "",
    }
    cols.update(leads_cfg.get("columns", {}) or {})

    # Meta API settings
    access_token = meta_cfg.get("access_token", "") or None
    api_version = meta_cfg.get("api_version", "v25.0")
    config_form_ids: List[str] = meta_cfg.get("form_ids", [])
    lookback_days = args.lookback_days if args.lookback_days is not None else meta_cfg.get("lookback_days", 14)
    ad_id_map: Dict[str, str] = meta_cfg.get("ad_id_to_ad_name", {}) or {}

    # Form IDs: CLI overrides config
    form_ids: List[str] = args.form_ids or config_form_ids
    if not form_ids:
        raise SystemExit(
            "[CONFIG ERROR] No form IDs configured. "
            "Add form_ids to config.json under meta, or pass --form-id."
        )

    # Since date
    since_dt: Optional[datetime] = None
    if args.since:
        since_dt = parse_dt(args.since)
        if since_dt is None:
            raise SystemExit(
                f"[CONFIG ERROR] Could not parse --since date: {args.since!r}. "
                "Expected format: YYYY-MM-DD."
            )

    # Build clients
    try:
        meta_client = MetaLeadsClient(access_token=access_token, api_version=api_version)
    except ValueError as exc:
        raise SystemExit(f"[CONFIG ERROR] {exc}")

    grist_client = GristClient(server=server, doc_id=doc_id, api_key=api_key)

    if args.dry_run:
        print("[DRY RUN] No changes will be written to Grist.")

    try:
        stats = sync_meta_leads_to_grist(
            meta_client=meta_client,
            grist_client=grist_client,
            form_ids=form_ids,
            table_id=table_id,
            cols=cols,
            ad_id_map=ad_id_map,
            lookback_days=lookback_days,
            since=since_dt,
            dry_run=args.dry_run,
            verbose_pii=args.verbose_pii,
            allow_no_meta_id=args.allow_no_meta_id,
        )
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[FATAL] Unexpected error: {exc}")
        raise

    _print_summary(stats, dry_run=args.dry_run)

    if stats["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

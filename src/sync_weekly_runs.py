"""
Fetch weekly ad performance from Meta Marketing API and sync to Grist Weekly_runs.

Replaces the manual steps:
  4. Download weekly performance CSV from Ads Manager
  5. pixi run update_weekly_runs "file.csv"

Weeks run Thursday → Wednesday (same convention as the rest of the pipeline).
The Grist week formula:  d = Date - 3 days  →  ISO week of d.

Algorithm:
  1. Read existing Weekly_runs from Grist; find the most recent week.
  2. Re-sync that week from its Thursday (it may have been updated mid-week).
  3. Fetch every day through today from the Meta Marketing API.
  4. Aggregate daily rows into Thu-Wed buckets; incomplete current week is stored
     against its eventual Wednesday end date.
  5. Patch existing Grist records that need updating; insert new ones.

Required config additions (config.json → "meta" section):
  "ad_account_id":      "act_XXXXXXXXX"        # your Meta ad account ID
  "lead_action_types":  ["onsite_conversion.lead_grouped"]   # optional
  "lookback_weeks":     8                       # used only when Weekly_runs is empty

Usage:
  pixi run fetch_weekly_runs
  pixi run fetch_weekly_runs --dry-run
  pixi run fetch_weekly_runs --since 2026-05-01
  pixi run fetch_weekly_runs --auto-create-ads
"""

import argparse
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests

from grist.grist import GristClient
from utils import load_config


# ---------------------------------------------------------------------------
# Thu–Wed week helpers
# ---------------------------------------------------------------------------

def week_end_for_date(d: date) -> date:
    """Return the Wednesday that closes the Thu-Wed week containing d."""
    # Mon=0 … Sun=6; Thu=3.  days_since_thu wraps correctly via modulo.
    days_since_thu = (d.weekday() - 3) % 7
    thursday = d - timedelta(days=days_since_thu)
    return thursday + timedelta(days=6)  # +6 lands on Wednesday


def week_start_for_date(d: date) -> date:
    """Return the Thursday that opens the Thu-Wed week containing d."""
    days_since_thu = (d.weekday() - 3) % 7
    return d - timedelta(days=days_since_thu)


def date_to_unix(d: date) -> int:
    """Midnight UTC Unix timestamp for a date (Grist date storage format)."""
    return int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp())


def unix_to_date(ts: int) -> Optional[date]:
    """Convert a Grist UTC timestamp back to a date."""
    if not ts:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).date()


def week_label(end_date: date) -> str:
    """Week label string produced by the Grist formula (for logging only)."""
    d = end_date - timedelta(days=3)
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


# ---------------------------------------------------------------------------
# Meta Marketing API – insights client
# ---------------------------------------------------------------------------

class MetaInsightsClient:
    BASE_URL = "https://graph.facebook.com"

    def __init__(self, access_token: str, api_version: str = "v25.0") -> None:
        self.access_token = access_token
        self.api_version = api_version
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.BASE_URL}/{self.api_version}/{path.lstrip('/')}"

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        p = dict(params)
        p["access_token"] = self.access_token
        r = self.session.get(self._url(path), params=p, timeout=60)
        if not r.ok:
            try:
                err = r.json().get("error", {})
                msg = (
                    f"#{err.get('code')}/{err.get('error_subcode')}: "
                    f"{err.get('message', r.text[:300])}"
                )
            except Exception:
                msg = r.text[:300]
            if r.status_code in (401, 403):
                raise SystemExit(
                    f"[ERROR] Meta API auth error ({r.status_code}): {msg}\n"
                    "Check that META_ACCESS_TOKEN is valid and has ads_read permission."
                )
            if r.status_code == 429:
                raise SystemExit(
                    "[ERROR] Meta API rate limit hit. Wait a few minutes and retry."
                )
            raise SystemExit(f"[ERROR] Meta API error ({r.status_code}): {msg}")
        return r.json()

    def fetch_daily_insights(
        self,
        ad_account_id: str,
        since: date,
        until: date,
    ) -> List[Dict[str, Any]]:
        """
        Fetch daily ad-level insights from the Meta Marketing API.

        Each returned row has at minimum: ad_name, date_stop, spend, actions.
        Results are cursor-paginated automatically.
        """
        params: Dict[str, Any] = {
            "level": "ad",
            "fields": "ad_name,spend,actions,date_stop",
            "time_range": f'{{"since":"{since.isoformat()}","until":"{until.isoformat()}"}}',
            "time_increment": "1",
            "limit": 500,
        }

        results: List[Dict[str, Any]] = []
        current_params = dict(params)

        while True:
            data = self._get(f"{ad_account_id}/insights", current_params)
            page = data.get("data", [])
            results.extend(page)

            cursors = data.get("paging", {}).get("cursors", {})
            after = cursors.get("after")
            if not after or not page:
                break
            current_params = dict(params)
            current_params["after"] = after

        return results


# ---------------------------------------------------------------------------
# Aggregation: daily → Thu-Wed weeks
# ---------------------------------------------------------------------------

def aggregate_to_weeks(
    daily_rows: List[Dict[str, Any]],
    lead_action_types: List[str],
) -> Dict[Tuple[str, date], Dict[str, Any]]:
    """
    Group daily ad-level rows into Thu-Wed week buckets.

    Returns {(ad_name, week_end_wednesday): {"spend": float, "leads": int}}.
    """
    buckets: Dict[Tuple[str, date], Dict[str, Any]] = defaultdict(
        lambda: {"spend": 0.0, "leads": 0}
    )

    for row in daily_rows:
        ad_name = (row.get("ad_name") or "").strip()
        date_stop_str = (row.get("date_stop") or "").strip()
        if not ad_name or not date_stop_str:
            continue

        try:
            row_date = date.fromisoformat(date_stop_str)
        except ValueError:
            continue

        key = (ad_name, week_end_for_date(row_date))

        try:
            buckets[key]["spend"] += float(row.get("spend") or 0)
        except (TypeError, ValueError):
            pass

        for action in row.get("actions") or []:
            if action.get("action_type") in lead_action_types:
                try:
                    buckets[key]["leads"] += int(float(action.get("value") or 0))
                except (TypeError, ValueError):
                    pass

    return dict(buckets)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Fetch weekly ad performance from Meta Marketing API "
            "and sync into Grist Weekly_runs."
        )
    )
    ap.add_argument("--config", default="config.json", help="Path to config.json")
    ap.add_argument(
        "--since",
        metavar="YYYY-MM-DD",
        help=(
            "Earliest date to fetch (overrides automatic lookback from last Grist week). "
            "Aligned to the Thursday that starts its week."
        ),
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing to Grist.",
    )
    ap.add_argument(
        "--auto-create-ads",
        action="store_true",
        help="Create missing ads in the Grist Ads table automatically.",
    )
    args = ap.parse_args()

    cfg = load_config(args.config)
    ad_cfg = cfg["ad_tracking"]
    meta_cfg = cfg.get("meta", {})

    # Resolve Meta access token
    token_env = meta_cfg.get("access_token_env", "META_ACCESS_TOKEN")
    access_token = meta_cfg.get("access_token") or os.environ.get(token_env, "")
    if not access_token:
        raise SystemExit(
            f"[ERROR] Meta access token not found.\n"
            f"Set the {token_env} environment variable, "
            "or add 'access_token' to config.json under 'meta'."
        )

    ad_account_id = meta_cfg.get("ad_account_id", "")
    if not ad_account_id:
        raise SystemExit(
            "[ERROR] 'ad_account_id' missing from config.json under 'meta'.\n"
            'Example: "ad_account_id": "act_123456789"'
        )

    api_version = meta_cfg.get("api_version", "v25.0")
    lead_action_types: List[str] = meta_cfg.get(
        "lead_action_types", ["onsite_conversion.lead_grouped", "lead"]
    )
    lookback_weeks = int(meta_cfg.get("lookback_weeks", 8))

    ads_table_id = ad_cfg.get("ads_table_id", "Ads")
    ad_name_col = ad_cfg.get("columns", {}).get("ad_name", "Name")

    grist = GristClient(
        ad_cfg["doc_id"],
        ad_cfg["api_key"],
        ad_cfg.get("server", "https://docs.getgrist.com"),
    )
    meta = MetaInsightsClient(access_token, api_version)

    today = date.today()

    # ------------------------------------------------------------------
    # Determine sync date range
    # ------------------------------------------------------------------
    print("[INFO] Fetching existing Weekly_runs from Grist...")
    existing_records = grist.fetch_records("Weekly_runs", flat=True)

    last_week_ts: Optional[int] = None
    if existing_records:
        timestamps = [r.get("Week") for r in existing_records if r.get("Week")]
        if timestamps:
            last_week_ts = max(int(t) for t in timestamps)

    if args.since:
        try:
            anchor = date.fromisoformat(args.since)
        except ValueError:
            raise SystemExit(f"[ERROR] Invalid --since date: {args.since!r}")
        sync_from = week_start_for_date(anchor)
        print(f"[INFO] --since override: fetching from {sync_from} (Thursday of that week).")
    elif last_week_ts:
        last_week_end = unix_to_date(last_week_ts)
        sync_from = week_start_for_date(last_week_end)  # Thursday of last Grist week
        print(
            f"[INFO] Last week in Grist: {week_label(last_week_end)} "
            f"(ends {last_week_end}). Re-syncing from {sync_from} to pick up any updates."
        )
    else:
        sync_from = week_start_for_date(today - timedelta(weeks=lookback_weeks))
        print(
            f"[INFO] No existing Weekly_runs found. "
            f"Fetching last {lookback_weeks} weeks from {sync_from}."
        )

    sync_until = today
    print(f"[INFO] Date range: {sync_from} → {sync_until}")

    # ------------------------------------------------------------------
    # Fetch from Meta
    # ------------------------------------------------------------------
    print(f"[INFO] Querying Meta Marketing API ({api_version})...")
    daily_rows = meta.fetch_daily_insights(ad_account_id, sync_from, sync_until)
    print(f"[INFO] Received {len(daily_rows)} daily ad-rows from Meta.")

    if not daily_rows:
        print("[WARN] No data returned from Meta for this date range. Nothing to sync.")
        return

    # ------------------------------------------------------------------
    # Aggregate into Thu-Wed weeks
    # ------------------------------------------------------------------
    aggregated = aggregate_to_weeks(daily_rows, lead_action_types)
    print(f"[INFO] Aggregated into {len(aggregated)} (ad, week) buckets.")

    # ------------------------------------------------------------------
    # Load Grist Ads table for name → record-ID mapping
    # ------------------------------------------------------------------
    print("[INFO] Fetching Ads table from Grist...")
    ads_records = grist.fetch_records(ads_table_id, flat=True)
    ad_name_to_id: Dict[str, int] = {
        (r.get(ad_name_col) or "").strip(): r["id"]
        for r in ads_records
        if (r.get(ad_name_col) or "").strip() and r.get("id")
    }
    print(f"[INFO] Found {len(ad_name_to_id)} ads in Grist.")

    # ------------------------------------------------------------------
    # Handle ads present in Meta data but missing from Grist
    # ------------------------------------------------------------------
    missing_ad_names = sorted(
        {name for (name, _) in aggregated if name not in ad_name_to_id}
    )
    if missing_ad_names:
        if args.auto_create_ads and not args.dry_run:
            print(f"[INFO] Creating {len(missing_ad_names)} missing ads in Grist:")
            for name in missing_ad_names:
                print(f"  + {name}")
            grist.add_records(
                ads_table_id,
                [{"fields": {ad_name_col: n}} for n in missing_ad_names],
            )
            ads_records = grist.fetch_records(ads_table_id, flat=True)
            ad_name_to_id = {
                (r.get(ad_name_col) or "").strip(): r["id"]
                for r in ads_records
                if (r.get(ad_name_col) or "").strip() and r.get("id")
            }
        else:
            print(f"[WARN] {len(missing_ad_names)} ads from Meta not in Grist Ads table:")
            for name in missing_ad_names:
                print(f"  - {name}")
            if not args.auto_create_ads:
                print("[WARN] Use --auto-create-ads to create them automatically.")

    # ------------------------------------------------------------------
    # Build existing-record lookup: (week_ts, ad_id) → grist_record_id
    # ------------------------------------------------------------------
    existing_lookup: Dict[Tuple[int, int], int] = {}
    for rec in existing_records:
        w = rec.get("Week")
        a = rec.get("Ad")
        i = rec.get("id")
        if w and a and i:
            existing_lookup[(int(w), int(a))] = i

    # ------------------------------------------------------------------
    # Classify each aggregated bucket as INSERT or UPDATE
    # ------------------------------------------------------------------
    to_insert: List[Dict[str, Any]] = []
    to_update: List[Dict[str, Any]] = []
    skipped: List[str] = []

    for (ad_name, wk_end), metrics in sorted(
        aggregated.items(), key=lambda x: (x[0][1], x[0][0])
    ):
        ad_id = ad_name_to_id.get(ad_name)
        if ad_id is None:
            skipped.append(f"{ad_name} @ {week_label(wk_end)}")
            continue

        week_ts = date_to_unix(wk_end)
        is_partial = wk_end > today
        tag = " [partial]" if is_partial else ""

        fields: Dict[str, Any] = {
            "Week": week_ts,
            "Ad": ad_id,
            "Spend": round(metrics["spend"], 2),
            "Leads": metrics["leads"],
        }

        existing_id = existing_lookup.get((week_ts, ad_id))
        if existing_id is not None:
            to_update.append({"id": existing_id, "fields": fields})
            action = "UPDATE"
        else:
            to_insert.append({"fields": fields})
            action = "INSERT"

        print(
            f"  [{action}]{tag} {week_label(wk_end)} (ends {wk_end})  "
            f"{ad_name}: spend={metrics['spend']:.2f} ILS, leads={metrics['leads']}"
        )

    print(f"\n[SUMMARY]")
    print(f"  To insert : {len(to_insert)}")
    print(f"  To update : {len(to_update)}")
    print(f"  Skipped   : {len(skipped)} (ad not in Grist)")

    if skipped:
        print("  Skipped entries:")
        for s in skipped:
            print(f"    - {s}")

    if args.dry_run:
        print("\n[DRY RUN] No changes written to Grist.")
        return

    if to_update:
        print(f"\n[INFO] Patching {len(to_update)} existing records in Weekly_runs...")
        grist.patch_records("Weekly_runs", to_update)

    if to_insert:
        print(f"[INFO] Inserting {len(to_insert)} new records into Weekly_runs...")
        grist.add_records("Weekly_runs", to_insert)

    if not to_update and not to_insert:
        print("\n[INFO] Nothing to write — Grist is already up to date.")
    else:
        print("[SUCCESS] Weekly_runs synced.")


if __name__ == "__main__":
    main()

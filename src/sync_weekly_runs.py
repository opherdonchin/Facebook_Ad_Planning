"""
Fetch weekly ad performance from Meta Marketing API and sync to Grist Weekly_runs.

Replaces the manual steps:
  4. Download weekly performance CSV from Ads Manager
  5. pixi run update_weekly_runs "file.csv"

Weeks run Thursday → Wednesday (same convention as the rest of the pipeline).
The Grist week formula:  d = Date - 3 days  →  ISO week of d.

Algorithm:
  1. Capture an exact Thursday-through-Wednesday Meta range as raw daily rows.
  2. Record the account timezone, range, capture time, configuration, and checksum
     in a frozen source snapshot while printing a dry-run preview.
  3. Reconcile that snapshot independently with Ads Manager.
  4. Replay only the checksummed snapshot for a Grist write.
  5. Aggregate daily rows into Thu-Wed buckets, then patch existing Weekly_runs
     records or insert new ones.

Required config additions (config.json → "meta" section):
  "ad_account_id":      "act_XXXXXXXXX"        # your Meta ad account ID
  "lead_action_types":  ["onsite_conversion.lead_grouped", "lead"]  # optional
  "lookback_weeks":     8                       # used only when Weekly_runs is empty

Usage:
  # Capture one exact, read-only source snapshot for reconciliation:
  pixi run fetch_weekly_runs --since 2026-09-10 --until 2026-09-16 \
      --snapshot-out outputs/meta_2026-09-10_2026-09-16.json --dry-run

  # After reconciling that file with Ads Manager, write those exact rows:
  pixi run fetch_weekly_runs --since 2026-09-10 --until 2026-09-16 \
      --snapshot-in outputs/meta_2026-09-10_2026-09-16.json

  # A live diagnostic dry run is still supported, but cannot be written:
  pixi run fetch_weekly_runs --dry-run
"""

import argparse
import hashlib
import hmac
import json
import os
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests

from grist.grist import GristClient
from utils import load_config


SNAPSHOT_SCHEMA_VERSION = 1
SNAPSHOT_CHECKSUM_FIELD = "payload_sha256"
AggregateKey = Tuple[str, str, date]


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
# Frozen Meta source snapshots
# ---------------------------------------------------------------------------

def parse_iso_date(value: str, option_name: str) -> date:
    """Parse one required ISO date and produce a CLI-friendly error."""
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {option_name} date: {value!r}") from None


def validate_date_range(since: date, until: date) -> None:
    """Require a non-empty inclusive reporting range."""
    if until < since:
        raise ValueError(
            f"Invalid reporting range: --until {until} is before --since {since}."
        )


def validate_weekly_reporting_range(since: date, until: date) -> None:
    """Require one or more complete Thu-Wed reporting windows."""
    validate_date_range(since, until)
    if since.weekday() != 3 or until.weekday() != 2:
        raise ValueError(
            "An explicit weekly reporting range must start on Thursday and end "
            f"on Wednesday; found {since} through {until}."
        )
    if (until - since).days % 7 != 6:
        raise ValueError(
            "An explicit weekly reporting range must contain whole Thu-Wed weeks."
        )


def validate_daily_rows_range(
    daily_rows: List[Dict[str, Any]],
    since: date,
    until: date,
) -> None:
    """Ensure every captured daily row belongs to the declared source range."""
    for index, row in enumerate(daily_rows):
        if not isinstance(row, dict):
            raise ValueError(f"Meta daily row {index} is not an object.")
        raw_date = row.get("date_stop")
        try:
            row_date = date.fromisoformat(raw_date)
        except (TypeError, ValueError):
            raise ValueError(
                f"Meta daily row {index} has invalid date_stop {raw_date!r}."
            ) from None
        if not since <= row_date <= until:
            raise ValueError(
                f"Meta daily row {index} date_stop {row_date} falls outside "
                f"the declared range {since} through {until}."
            )
        raw_start = row.get("date_start")
        if raw_start is not None and raw_start != raw_date:
            raise ValueError(
                f"Meta daily row {index} is not a one-day row: "
                f"date_start={raw_start!r}, date_stop={raw_date!r}."
            )


def _canonical_snapshot_payload(snapshot: Dict[str, Any]) -> bytes:
    payload = {
        key: value
        for key, value in snapshot.items()
        if key != SNAPSHOT_CHECKSUM_FIELD
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def snapshot_checksum(snapshot: Dict[str, Any]) -> str:
    """Return the SHA-256 checksum for all snapshot fields except the checksum."""
    return hashlib.sha256(_canonical_snapshot_payload(snapshot)).hexdigest()


def build_source_snapshot(
    *,
    ad_account_id: str,
    account_timezone: str,
    since: date,
    until: date,
    api_version: str,
    lead_action_types: List[str],
    daily_rows: List[Dict[str, Any]],
    captured_at_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build a checksummed, self-describing snapshot of raw Meta daily rows."""
    validate_date_range(since, until)
    if not ad_account_id:
        raise ValueError("Snapshot ad account ID cannot be empty.")
    if not account_timezone:
        raise ValueError("Snapshot account timezone cannot be empty.")
    validate_lead_action_types(lead_action_types)
    validate_daily_rows_range(daily_rows, since, until)

    captured = captured_at_utc or datetime.now(timezone.utc)
    if captured.tzinfo is None or captured.utcoffset() is None:
        raise ValueError("Snapshot capture time must be timezone-aware UTC.")
    captured = captured.astimezone(timezone.utc).replace(microsecond=0)

    # Round-trip through JSON so the checksummed value is exactly what can be
    # persisted and loaded later, rather than a caller-owned mutable object.
    normalized_rows = json.loads(json.dumps(daily_rows, ensure_ascii=False))
    snapshot: Dict[str, Any] = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source": "Meta Marketing API daily ad insights",
        "ad_account_id": ad_account_id,
        "account_timezone": account_timezone,
        "since": since.isoformat(),
        "until": until.isoformat(),
        "captured_at_utc": captured.isoformat().replace("+00:00", "Z"),
        "api_version": api_version,
        "lead_action_types": list(lead_action_types),
        "daily_rows": normalized_rows,
    }
    snapshot[SNAPSHOT_CHECKSUM_FIELD] = snapshot_checksum(snapshot)
    return snapshot


def write_source_snapshot(path: Path, snapshot: Dict[str, Any]) -> None:
    """Write a new immutable-by-convention snapshot without overwriting one."""
    stored_checksum = snapshot.get(SNAPSHOT_CHECKSUM_FIELD)
    if not isinstance(stored_checksum, str) or not hmac.compare_digest(
        stored_checksum, snapshot_checksum(snapshot)
    ):
        raise ValueError("Refusing to write a source snapshot with a bad checksum.")
    if path.exists():
        raise ValueError(f"Snapshot already exists and will not be overwritten: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_source_snapshot(
    path: Path,
    *,
    expected_account_id: str,
    expected_since: date,
    expected_until: date,
    expected_account_timezone: Optional[str] = None,
    expected_lead_action_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Load and validate a frozen source snapshot before it can be used."""
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read Meta source snapshot {path}: {exc}") from exc
    if not isinstance(snapshot, dict):
        raise ValueError(f"Meta source snapshot {path} is not a JSON object.")

    if snapshot.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError(
            f"Unsupported Meta source snapshot schema: "
            f"{snapshot.get('schema_version')!r}."
        )
    stored_checksum = snapshot.get(SNAPSHOT_CHECKSUM_FIELD)
    if not isinstance(stored_checksum, str) or not hmac.compare_digest(
        stored_checksum, snapshot_checksum(snapshot)
    ):
        raise ValueError(f"Meta source snapshot checksum mismatch: {path}")

    if snapshot.get("ad_account_id") != expected_account_id:
        raise ValueError(
            "Meta source snapshot account mismatch: "
            f"expected {expected_account_id!r}, found "
            f"{snapshot.get('ad_account_id')!r}."
        )
    if snapshot.get("since") != expected_since.isoformat() or snapshot.get(
        "until"
    ) != expected_until.isoformat():
        raise ValueError(
            "Meta source snapshot range mismatch: "
            f"expected {expected_since} through {expected_until}, found "
            f"{snapshot.get('since')!r} through {snapshot.get('until')!r}."
        )
    snapshot_timezone = snapshot.get("account_timezone")
    if not isinstance(snapshot_timezone, str) or not snapshot_timezone:
        raise ValueError("Meta source snapshot has no account timezone.")
    if (
        expected_account_timezone
        and snapshot_timezone != expected_account_timezone
    ):
        raise ValueError(
            "Meta source snapshot timezone mismatch: "
            f"expected {expected_account_timezone!r}, found {snapshot_timezone!r}."
        )
    snapshot_action_types = snapshot.get("lead_action_types")
    try:
        validate_lead_action_types(snapshot_action_types)
    except ValueError as exc:
        raise ValueError(f"Meta source snapshot has invalid lead actions: {exc}") from exc
    if (
        expected_lead_action_types is not None
        and snapshot_action_types != expected_lead_action_types
    ):
        raise ValueError(
            "Meta source snapshot lead-action configuration mismatch: "
            f"expected {expected_lead_action_types!r}, found "
            f"{snapshot_action_types!r}."
        )

    captured_at = snapshot.get("captured_at_utc")
    try:
        captured = datetime.fromisoformat(str(captured_at).replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(
            f"Meta source snapshot has invalid captured_at_utc {captured_at!r}."
        ) from None
    if captured.utcoffset() != timedelta(0):
        raise ValueError("Meta source snapshot capture time is not UTC.")

    daily_rows = snapshot.get("daily_rows")
    if not isinstance(daily_rows, list):
        raise ValueError("Meta source snapshot daily_rows is not a list.")
    validate_daily_rows_range(daily_rows, expected_since, expected_until)
    return snapshot


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

        Each returned row has at minimum: ad_id, ad_name, date_start,
        date_stop, spend, and actions.
        Results are cursor-paginated automatically.
        """
        params: Dict[str, Any] = {
            "level": "ad",
            "fields": "ad_id,ad_name,spend,actions,date_start,date_stop",
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

    def fetch_account_timezone(self, ad_account_id: str) -> str:
        """Fetch the timezone that controls Meta's reporting-date boundaries."""
        account = self._get(ad_account_id, {"fields": "timezone_name"})
        timezone_name = account.get("timezone_name")
        if not isinstance(timezone_name, str) or not timezone_name.strip():
            raise ValueError(
                f"Meta ad account {ad_account_id!r} returned no timezone_name."
            )
        return timezone_name.strip()


# ---------------------------------------------------------------------------
# Aggregation: daily → Thu-Wed weeks
# ---------------------------------------------------------------------------

def parse_lead_count(value: Any, context: str) -> int:
    """Parse Meta's count without truncation or silent fallback."""
    if value is None or isinstance(value, bool):
        raise ValueError(f"Invalid Meta lead count for {context}: {value!r}.")
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid Meta lead count for {context}: {value!r}.") from None
    if not parsed.is_finite() or parsed < 0 or parsed != parsed.to_integral_value():
        raise ValueError(
            f"Meta lead count for {context} must be a nonnegative integer; "
            f"found {value!r}."
        )
    return int(parsed)


def parse_spend_amount(value: Any, context: str) -> Decimal:
    """Parse Meta spend exactly and reject missing or unsafe values."""
    if value is None or isinstance(value, bool):
        raise ValueError(f"Invalid Meta spend for {context}: {value!r}.")
    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValueError(f"Invalid Meta spend for {context}: {value!r}.") from None
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(
            f"Meta spend for {context} must be a finite nonnegative amount; "
            f"found {value!r}."
        )
    return parsed


def validate_lead_action_types(lead_action_types: List[str]) -> None:
    if (
        not isinstance(lead_action_types, list)
        or not lead_action_types
        or any(not isinstance(value, str) or not value for value in lead_action_types)
        or len(set(lead_action_types)) != len(lead_action_types)
    ):
        raise ValueError(
            "lead_action_types must be a non-empty ordered list of unique names."
        )


def aggregate_to_weeks(
    daily_rows: List[Dict[str, Any]],
    lead_action_types: List[str],
) -> Dict[AggregateKey, Dict[str, Any]]:
    """
    Group daily ad-level rows into Thu-Wed week buckets.

    ``lead_action_types`` is an ordered fallback list, not a list of additive
    metrics. Meta commonly returns one Instant Form submission under both
    ``onsite_conversion.lead_grouped`` and ``lead``. In that case we use the
    first configured type and count the submission once. If the aliases are
    both present but disagree, stop rather than silently choosing a number.

    Returns {(meta_ad_id, ad_name, week_end_wednesday): metrics}. Meta IDs and
    names are both retained, and a one-to-one ID/name relationship is required
    within a snapshot so renamed or duplicate-name ads cannot be merged.
    """
    validate_lead_action_types(lead_action_types)
    buckets: Dict[AggregateKey, Dict[str, Any]] = defaultdict(
        lambda: {"spend": Decimal("0"), "leads": 0}
    )
    names_by_ad_id: Dict[str, str] = {}
    ad_ids_by_name: Dict[str, str] = {}
    seen_daily_rows: Set[Tuple[str, date]] = set()

    for row_index, row in enumerate(daily_rows):
        if not isinstance(row, dict):
            raise ValueError(f"Meta daily row {row_index} is not an object.")
        meta_ad_id = str(row.get("ad_id") or "").strip()
        ad_name = (row.get("ad_name") or "").strip()
        date_stop_str = (row.get("date_stop") or "").strip()
        if not meta_ad_id or not ad_name or not date_stop_str:
            raise ValueError(
                f"Meta daily row {row_index} is missing ad_id, ad_name, or date_stop."
            )

        try:
            row_date = date.fromisoformat(date_stop_str)
        except ValueError:
            raise ValueError(
                f"Meta daily row {row_index} has invalid date_stop "
                f"{date_stop_str!r}."
            ) from None

        daily_key = (meta_ad_id, row_date)
        if daily_key in seen_daily_rows:
            raise ValueError(
                f"Duplicate Meta daily row for ad {meta_ad_id!r} ({ad_name}) "
                f"on {date_stop_str}."
            )
        seen_daily_rows.add(daily_key)

        prior_name = names_by_ad_id.setdefault(meta_ad_id, ad_name)
        if prior_name != ad_name:
            raise ValueError(
                f"Meta ad ID {meta_ad_id!r} has multiple names in one snapshot: "
                f"{prior_name!r} and {ad_name!r}."
            )
        prior_id = ad_ids_by_name.setdefault(ad_name, meta_ad_id)
        if prior_id != meta_ad_id:
            raise ValueError(
                f"Meta ad name {ad_name!r} maps to multiple IDs in one snapshot: "
                f"{prior_id!r} and {meta_ad_id!r}."
            )

        key = (meta_ad_id, ad_name, week_end_for_date(row_date))

        spend_context = f"ad {meta_ad_id!r} ({ad_name}) on {date_stop_str}"
        buckets[key]["spend"] += parse_spend_amount(
            row.get("spend"), spend_context
        )

        lead_counts: Dict[str, int] = {}
        actions = row.get("actions")
        if actions is None:
            actions = []
        if not isinstance(actions, list):
            raise ValueError(
                f"Meta actions for ad {meta_ad_id!r} ({ad_name}) on "
                f"{date_stop_str} are not a list."
            )
        for action_index, action in enumerate(actions):
            if not isinstance(action, dict):
                raise ValueError(
                    f"Meta action {action_index} for ad {meta_ad_id!r} "
                    f"({ad_name}) on {date_stop_str} is not an object."
                )
            action_type = action.get("action_type")
            if action_type not in lead_action_types:
                continue
            if action_type in lead_counts:
                raise ValueError(
                    f"Meta lead action {action_type!r} appears more than once for "
                    f"ad {meta_ad_id!r} ({ad_name}) on {date_stop_str}."
                )
            context = (
                f"ad {meta_ad_id!r} ({ad_name}) on {date_stop_str}, "
                f"action {action_type!r}"
            )
            lead_counts[action_type] = parse_lead_count(action.get("value"), context)

        present_counts = {
            action_type: lead_counts[action_type]
            for action_type in lead_action_types
            if action_type in lead_counts
        }
        if len(set(present_counts.values())) > 1:
            raise ValueError(
                "Meta lead action aliases disagree for "
                f"{ad_name} on {date_stop_str}: {present_counts}. "
                "Review the Results metric before syncing."
            )

        for action_type in lead_action_types:
            if action_type in present_counts:
                buckets[key]["leads"] += present_counts[action_type]
                break

    return dict(buckets)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
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
        "--until",
        metavar="YYYY-MM-DD",
        help=(
            "Last inclusive Meta account date to fetch. Requires --since; "
            "when provided, the two dates are used exactly without alignment."
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
    snapshots = ap.add_mutually_exclusive_group()
    snapshots.add_argument(
        "--snapshot-out",
        type=Path,
        help=(
            "Write the exact raw Meta response and source metadata to a new, "
            "checksummed JSON file. Requires --since, --until, and --dry-run."
        ),
    )
    snapshots.add_argument(
        "--snapshot-in",
        type=Path,
        help=(
            "Use a previously captured snapshot for planning or writing. No "
            "Meta request is made. Requires matching --since and --until."
        ),
    )
    return ap


def build_existing_weekly_lookup(
    existing_records: List[Dict[str, Any]],
) -> Dict[Tuple[int, int], int]:
    """Map canonical week/ad pairs to records and reject logical duplicates."""
    result: Dict[Tuple[int, int], int] = {}
    source_weeks: Dict[Tuple[int, int], Any] = {}
    for rec in existing_records:
        raw_week = rec.get("Week")
        raw_ad = rec.get("Ad")
        record_id = rec.get("id")
        if not raw_week or not raw_ad or not record_id:
            continue

        record_date = unix_to_date(int(raw_week))
        if record_date is None:
            continue
        canonical_week_ts = date_to_unix(week_end_for_date(record_date))
        lookup_key = (canonical_week_ts, int(raw_ad))
        if lookup_key in result:
            canonical_date = unix_to_date(canonical_week_ts)
            raise ValueError(
                "Duplicate Grist Weekly_runs rows for canonical week "
                f"ending {canonical_date} and ad record {lookup_key[1]}: "
                f"record {result[lookup_key]} has Week={source_weeks[lookup_key]!r}; "
                f"record {record_id} has Week={raw_week!r}."
            )
        result[lookup_key] = int(record_id)
        source_weeks[lookup_key] = raw_week
    return result


def main() -> None:
    ap = build_arg_parser()
    args = ap.parse_args()

    if args.until and not args.since:
        ap.error("--until requires --since.")
    if (args.snapshot_in or args.snapshot_out) and not (args.since and args.until):
        ap.error("Snapshot modes require both --since and --until.")
    if args.snapshot_out and not args.dry_run:
        ap.error("--snapshot-out is capture-only and requires --dry-run.")
    if not args.dry_run and not args.snapshot_in:
        ap.error(
            "A write must use --snapshot-in so Grist receives the exact data "
            "that was reconciled. Capture it first with --snapshot-out --dry-run."
        )

    cfg = load_config(args.config)
    ad_cfg = cfg["ad_tracking"]
    meta_cfg = cfg.get("meta", {})

    ad_account_id = str(meta_cfg.get("ad_account_id") or "").strip()
    if not ad_account_id:
        raise SystemExit(
            "[ERROR] 'ad_account_id' missing from config.json under 'meta'.\n"
            'Example: "ad_account_id": "act_123456789"'
        )

    api_version = meta_cfg.get("api_version", "v25.0")
    lead_action_types: List[str] = meta_cfg.get(
        "lead_action_types", ["onsite_conversion.lead_grouped", "lead"]
    )
    validate_lead_action_types(lead_action_types)
    lookback_weeks = int(meta_cfg.get("lookback_weeks", 8))
    configured_account_timezone = meta_cfg.get("account_timezone")

    explicit_since: Optional[date] = None
    explicit_until: Optional[date] = None
    if args.since:
        try:
            explicit_since = parse_iso_date(args.since, "--since")
        except ValueError as exc:
            raise SystemExit(f"[ERROR] {exc}") from exc
    if args.until:
        try:
            explicit_until = parse_iso_date(args.until, "--until")
        except ValueError as exc:
            raise SystemExit(f"[ERROR] {exc}") from exc
    if explicit_since is not None and explicit_until is not None:
        try:
            validate_weekly_reporting_range(explicit_since, explicit_until)
        except ValueError as exc:
            raise SystemExit(f"[ERROR] {exc}") from exc

    ads_table_id = ad_cfg.get("ads_table_id", "Ads")
    ad_name_col = ad_cfg.get("columns", {}).get("ad_name", "Name")

    configured_server = ad_cfg.get("server")
    if not isinstance(configured_server, str) or not configured_server.strip():
        raise SystemExit(
            "[ERROR] 'server' missing from config.json under 'ad_tracking'.\n"
            "Set it to the exact Grist site that owns the configured document."
        )
    grist = GristClient(
        ad_cfg["doc_id"],
        ad_cfg["api_key"],
        configured_server.strip(),
    )

    today = date.today()

    snapshot: Optional[Dict[str, Any]] = None
    daily_rows: Optional[List[Dict[str, Any]]] = None
    account_timezone: Optional[str] = None
    if args.snapshot_in:
        assert explicit_since is not None and explicit_until is not None
        try:
            snapshot = load_source_snapshot(
                args.snapshot_in,
                expected_account_id=ad_account_id,
                expected_since=explicit_since,
                expected_until=explicit_until,
                expected_account_timezone=configured_account_timezone,
                expected_lead_action_types=lead_action_types,
            )
        except ValueError as exc:
            raise SystemExit(f"[ERROR] {exc}") from exc
        daily_rows = snapshot["daily_rows"]
        account_timezone = snapshot["account_timezone"]
        print(
            f"[INFO] Using frozen Meta snapshot {args.snapshot_in} "
            f"({snapshot[SNAPSHOT_CHECKSUM_FIELD]})."
        )
        print(
            f"[INFO] Snapshot captured {snapshot['captured_at_utc']} for "
            f"account timezone {account_timezone}."
        )

    # ------------------------------------------------------------------
    # Determine sync date range
    # ------------------------------------------------------------------
    existing_records: Optional[List[Dict[str, Any]]] = None
    if explicit_since is not None and explicit_until is not None:
        sync_from = explicit_since
        sync_until = explicit_until
        print(f"[INFO] Exact reporting range: {sync_from} → {sync_until}")
    else:
        print("[INFO] Fetching existing Weekly_runs from Grist...")
        existing_records = grist.fetch_records("Weekly_runs", flat=True)
        last_week_ts: Optional[int] = None
        if existing_records:
            timestamps = [r.get("Week") for r in existing_records if r.get("Week")]
            if timestamps:
                last_week_ts = max(int(t) for t in timestamps)

        if explicit_since is not None:
            sync_from = week_start_for_date(explicit_since)
            sync_until = today
            print(
                f"[INFO] --since override: fetching from {sync_from} "
                "(Thursday of that week)."
            )
        elif last_week_ts:
            last_week_end = unix_to_date(last_week_ts)
            sync_from = week_start_for_date(last_week_end)
            sync_until = today
            print(
                f"[INFO] Last week in Grist: {week_label(last_week_end)} "
                f"(ends {last_week_end}). Re-syncing from {sync_from} "
                "to pick up any updates."
            )
        else:
            sync_from = week_start_for_date(today - timedelta(weeks=lookback_weeks))
            sync_until = today
            print(
                f"[INFO] No existing Weekly_runs found. "
                f"Fetching last {lookback_weeks} weeks from {sync_from}."
            )

    print(f"[INFO] Date range: {sync_from} → {sync_until}")

    # ------------------------------------------------------------------
    # Fetch from Meta or use the already-validated frozen snapshot
    # ------------------------------------------------------------------
    if daily_rows is None:
        token_env = meta_cfg.get("access_token_env", "META_ACCESS_TOKEN")
        access_token = meta_cfg.get("access_token") or os.environ.get(token_env, "")
        if not access_token:
            raise SystemExit(
                f"[ERROR] Meta access token not found.\n"
                f"Set the {token_env} environment variable, "
                "or add 'access_token' to config.json under 'meta'."
            )
        meta = MetaInsightsClient(access_token, api_version)
        print(f"[INFO] Querying Meta Marketing API ({api_version})...")
        account_timezone = meta.fetch_account_timezone(ad_account_id)
        daily_rows = meta.fetch_daily_insights(ad_account_id, sync_from, sync_until)
        print(f"[INFO] Received {len(daily_rows)} daily ad-rows from Meta.")
        print(f"[INFO] Meta account timezone: {account_timezone}")

        if args.snapshot_out:
            snapshot = build_source_snapshot(
                ad_account_id=ad_account_id,
                account_timezone=account_timezone,
                since=sync_from,
                until=sync_until,
                api_version=api_version,
                lead_action_types=lead_action_types,
                daily_rows=daily_rows,
            )
            try:
                write_source_snapshot(args.snapshot_out, snapshot)
            except ValueError as exc:
                raise SystemExit(f"[ERROR] {exc}") from exc
            print(
                f"[INFO] Wrote frozen Meta source snapshot: {args.snapshot_out}"
            )
            print(
                f"[INFO] Snapshot checksum: {snapshot[SNAPSHOT_CHECKSUM_FIELD]}"
            )

    if not daily_rows:
        print("[WARN] No data returned from Meta for this date range. Nothing to sync.")
        return

    if existing_records is None:
        print("[INFO] Fetching existing Weekly_runs from Grist...")
        existing_records = grist.fetch_records("Weekly_runs", flat=True)

    # ------------------------------------------------------------------
    # Aggregate into Thu-Wed weeks
    # ------------------------------------------------------------------
    aggregated = aggregate_to_weeks(daily_rows, lead_action_types)
    print(f"[INFO] Aggregated into {len(aggregated)} (ad, week) buckets.")

    # ------------------------------------------------------------------
    # Fail before any write if Grist already has duplicate weekly rows.
    # ------------------------------------------------------------------
    existing_lookup = build_existing_weekly_lookup(existing_records)

    # ------------------------------------------------------------------
    # Load Grist Ads table for name → record-ID mapping
    # ------------------------------------------------------------------
    print("[INFO] Fetching Ads table from Grist...")
    ads_records = grist.fetch_records(ads_table_id, flat=True)

    def unique_ad_name_map(records: List[Dict[str, Any]]) -> Dict[str, int]:
        result: Dict[str, int] = {}
        for record in records:
            name = (record.get(ad_name_col) or "").strip()
            record_id = record.get("id")
            if not name or not record_id:
                continue
            if name in result:
                raise ValueError(
                    f"Grist Ads contains duplicate name {name!r}; Meta ad IDs "
                    "cannot be mapped unambiguously."
                )
            result[name] = int(record_id)
        return result

    ad_name_to_id = unique_ad_name_map(ads_records)
    print(f"[INFO] Found {len(ad_name_to_id)} ads in Grist.")

    # ------------------------------------------------------------------
    # Handle ads present in Meta data but missing from Grist
    # ------------------------------------------------------------------
    missing_ad_names = sorted(
        {
            ad_name
            for (_meta_ad_id, ad_name, _week_end) in aggregated
            if ad_name not in ad_name_to_id
        }
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
            ad_name_to_id = unique_ad_name_map(ads_records)
        else:
            print(f"[WARN] {len(missing_ad_names)} ads from Meta not in Grist Ads table:")
            for name in missing_ad_names:
                print(f"  - {name}")
            if not args.auto_create_ads:
                print("[WARN] Use --auto-create-ads to create them automatically.")
            if not args.dry_run:
                raise SystemExit(
                    "[ERROR] Refusing a partial Weekly_runs write while Meta ads "
                    "are missing from Grist."
                )

    # ------------------------------------------------------------------
    # Classify each aggregated bucket as INSERT or UPDATE
    # ------------------------------------------------------------------
    to_insert: List[Dict[str, Any]] = []
    to_update: List[Dict[str, Any]] = []
    skipped: List[str] = []

    for (meta_ad_id, ad_name, wk_end), metrics in sorted(
        aggregated.items(), key=lambda x: (x[0][2], x[0][1], x[0][0])
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
            "Spend": float(round(metrics["spend"], 2)),
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
            f"{ad_name} [Meta {meta_ad_id}]: "
            f"spend={metrics['spend']:.2f} ILS, leads={metrics['leads']}"
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

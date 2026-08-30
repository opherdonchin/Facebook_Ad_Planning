"""Export Meta ad insights into local Thu-Wed weekly CSV files."""

import argparse
import csv
import os
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Tuple

from sync_weekly_runs import MetaInsightsClient, aggregate_to_weeks
from utils import load_config


WEEK_RANGES: List[Tuple[str, date, date]] = [
    ("2026-W26", date(2026, 6, 25), date(2026, 7, 1)),
    ("2026-W27", date(2026, 7, 2), date(2026, 7, 8)),
    ("2026-W28", date(2026, 7, 9), date(2026, 7, 15)),
    ("2026-W29", date(2026, 7, 16), date(2026, 7, 22)),
    ("2026-W30", date(2026, 7, 23), date(2026, 7, 29)),
    ("2026-W31", date(2026, 7, 30), date(2026, 8, 5)),
    ("2026-W32", date(2026, 8, 6), date(2026, 8, 12)),
    ("2026-W33", date(2026, 8, 13), date(2026, 8, 19)),
    ("2026-W34", date(2026, 8, 20), date(2026, 8, 26)),
    ("2026-W35", date(2026, 8, 27), date(2026, 9, 2)),
]


def row_for_export(label: str, start: date, end: date, ad_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "Week": label,
        "Reporting starts": start.isoformat(),
        "Reporting ends": end.isoformat(),
        "Ad name": ad_name,
        "Amount spent (ILS)": f"{float(metrics['spend']):.2f}",
        "Results": int(metrics["leads"]),
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "Week",
        "Reporting starts",
        "Reporting ends",
        "Ad name",
        "Amount spent (ILS)",
        "Results",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--output-dir", default="facebook_exports")
    ap.add_argument(
        "--today",
        default=date.today().isoformat(),
        help="Last date with available actuals; future days are not requested.",
    )
    args = ap.parse_args()

    cfg = load_config(args.config)
    meta_cfg = cfg.get("meta", {})
    token_env = meta_cfg.get("access_token_env", "META_ACCESS_TOKEN")
    access_token = meta_cfg.get("access_token") or os.environ.get(token_env, "")
    if not access_token:
        raise SystemExit(f"[ERROR] Meta access token not found in config or {token_env}.")

    ad_account_id = meta_cfg.get("ad_account_id", "")
    if not ad_account_id:
        raise SystemExit("[ERROR] meta.ad_account_id is missing from config.")

    actual_until = date.fromisoformat(args.today)
    fetch_since = WEEK_RANGES[0][1]
    fetch_until = min(WEEK_RANGES[-1][2], actual_until)

    client = MetaInsightsClient(access_token, meta_cfg.get("api_version", "v25.0"))
    daily_rows = client.fetch_daily_insights(ad_account_id, fetch_since, fetch_until)
    lead_action_types = meta_cfg.get(
        "lead_action_types", ["onsite_conversion.lead_grouped", "lead"]
    )
    aggregated = aggregate_to_weeks(daily_rows, lead_action_types)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_rows: List[Dict[str, Any]] = []
    for label, start, end in WEEK_RANGES:
        rows = [
            row_for_export(label, start, end, ad_name, metrics)
            for (ad_name, week_end), metrics in aggregated.items()
            if week_end == end
        ]
        rows.sort(key=lambda r: r["Ad name"])
        all_rows.extend(rows)
        write_csv(out_dir / f"ads_manager_{label}_{start}_{end}.csv", rows)

    write_csv(out_dir / "ads_manager_2026-W26_to_2026-W35.csv", all_rows)
    print(f"[INFO] Fetched {len(daily_rows)} daily ad rows from Meta.")
    print(f"[INFO] Wrote {len(all_rows)} weekly ad rows to {out_dir}.")
    if actual_until < WEEK_RANGES[-1][2]:
        print(
            f"[INFO] 2026-W35 is partial: requested actuals through {actual_until}, "
            f"bucketed under week ending {WEEK_RANGES[-1][2]}."
        )


if __name__ == "__main__":
    main()

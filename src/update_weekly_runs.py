import argparse
import csv
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from grist.grist import GristClient


def read_csv_with_encoding(path: str) -> List[Dict[str, Any]]:
    """
    Read a CSV file trying different encodings and delimiters.
    Facebook exports may be UTF-16 tab-delimited or UTF-8 comma-delimited.
    """
    configs = [
        ("utf-16", "\t"),
        ("utf-16-le", "\t"),
        ("utf-8", ","),
        ("utf-8", "\t"),
        ("latin-1", ","),
    ]

    for encoding, delimiter in configs:
        try:
            rows: List[Dict[str, Any]] = []
            with open(path, "r", encoding=encoding, errors="strict") as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    rows.append(row)

            # Validate that we actually parsed multiple columns
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


def parse_date_to_timestamp(date_str: str) -> int:
    """
    Parse a date string (YYYY-MM-DD) and return Unix timestamp at midnight (naive, Israel local time).
    """
    try:
        dt = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        # Naive datetime (no timezone), treating as Israel local time
        return int(dt.timestamp())
    except Exception as e:
        raise ValueError(f"Could not parse date '{date_str}': {e}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Import Facebook ad performance CSV to Grist Weekly_runs table."
    )
    ap.add_argument("csv_file", help="Path to Facebook ad performance CSV export")
    ap.add_argument("--config", default="config.json", help="Path to config.json")
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Print records but do not insert to Grist.",
    )
    args = ap.parse_args()

    # Load configuration
    from utils import load_config

    cfg = load_config(args.config)
    ad_cfg = cfg["ad_tracking"]

    # Initialize Grist client
    client = GristClient(
        ad_cfg["doc_id"],
        ad_cfg["api_key"],
        ad_cfg.get("server", "https://docs.getgrist.com"),
    )

    # Read CSV file
    print(f"[INFO] Reading CSV file: {args.csv_file}")
    csv_rows = read_csv_with_encoding(args.csv_file)

    if not csv_rows:
        print("[WARN] No rows found in CSV file.")
        return

    # Fetch Ads table to build ad_name -> record_id mapping
    print("[INFO] Fetching Ads table from Grist...")
    ads_records = client.fetch_records("Ads", flat=True)

    ad_name_to_id: Dict[str, int] = {}
    for rec in ads_records:
        ad_name = rec.get("Name", "").strip()
        rec_id = rec.get("id")
        if ad_name and rec_id:
            ad_name_to_id[ad_name] = rec_id

    print(f"[INFO] Found {len(ad_name_to_id)} ads in Grist Ads table")

    # Transform CSV rows to Grist records
    records_to_insert: List[Dict[str, Any]] = []
    skipped_rows: List[str] = []
    missing_ads = set()

    for row in csv_rows:
        # Extract fields from CSV (handle potential leading/trailing spaces in column names)
        ad_name = row.get("Ad name", "").strip()
        reporting_ends = row.get("Reporting ends", "").strip()
        amount_spent = row.get("Amount spent (ILS)", "").strip()
        results = row.get("Results", "").strip()

        # Skip rows without ad name
        if not ad_name:
            skipped_rows.append("Row with empty ad name")
            continue

        # Look up ad reference ID
        ad_ref_id = ad_name_to_id.get(ad_name)
        if ad_ref_id is None:
            missing_ads.add(ad_name)
            skipped_rows.append(f"Ad name not found in Grist: {ad_name}")
            continue

        # Parse date to timestamp
        try:
            week_timestamp = parse_date_to_timestamp(reporting_ends)
        except ValueError as e:
            skipped_rows.append(f"Invalid date for {ad_name}: {e}")
            continue

        # Parse spend (float)
        try:
            spend = float(amount_spent) if amount_spent else 0.0
        except ValueError:
            skipped_rows.append(f"Invalid spend value for {ad_name}: {amount_spent}")
            continue

        # Parse leads (int, default to 0 if empty)
        try:
            leads = int(results) if results else 0
        except ValueError:
            skipped_rows.append(f"Invalid results value for {ad_name}: {results}")
            continue

        # Build record for Grist (must be wrapped in "fields" key)
        record = {
            "fields": {
                "Week": week_timestamp,
                "Ad": ad_ref_id,
                "Spend": spend,
                "Leads": leads,
            }
        }
        records_to_insert.append(record)

    # Report summary
    print(f"\n[SUMMARY]")
    print(f"  Total CSV rows: {len(csv_rows)}")
    print(f"  Records to insert: {len(records_to_insert)}")
    print(f"  Skipped rows: {len(skipped_rows)}")

    if missing_ads:
        print(f"\n[WARN] Missing ad names in Grist Ads table:")
        for ad in sorted(missing_ads):
            print(f"  - {ad}")

    if args.dry_run:
        print("\n[DRY RUN] Would insert these records:")
        for i, rec in enumerate(records_to_insert[:5], 1):
            print(f"  {i}. {rec}")
        if len(records_to_insert) > 5:
            print(f"  ... and {len(records_to_insert) - 5} more")
        return

    # Insert records to Grist
    if records_to_insert:
        print(
            f"\n[INFO] Inserting {len(records_to_insert)} records to Weekly_runs table..."
        )
        client.add_records("Weekly_runs", records_to_insert)
        print("[SUCCESS] Records inserted successfully!")
    else:
        print("\n[WARN] No records to insert.")


if __name__ == "__main__":
    main()

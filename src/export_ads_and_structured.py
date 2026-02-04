"""
Unified export script: Exports Grist database and generates structured CSV files.

This script performs two sequential operations:
1. Export full Grist database to performance_data.json (via export_ads module)
2. Convert JSON to structured CSV tables (via export_structured_data module)
"""

import argparse
import sys
from pathlib import Path

# Add src to path if needed
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from export_ads import fetch_full_database_dump, save_export
from export_structured_data import main as export_structured
from grist.grist import GristClient
from utils import load_config


def main():
    """Main entry point for unified export."""
    parser = argparse.ArgumentParser(
        description="Export Grist data and generate structured data files"
    )
    parser.add_argument(
        "--no-attachments", action="store_true", help="Skip downloading attachments"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "parquet", "both"],
        default="csv",
        help="Output format for structured data (default: csv)",
    )
    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config("config.json")
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    # Read from ad_tracking section
    ad_config = config.get("ad_tracking", {})
    DOC_ID = ad_config.get("doc_id")
    API_KEY = ad_config.get("api_key")
    SERVER = ad_config.get("server", "https://docs.getgrist.com")

    if not DOC_ID or not API_KEY:
        print(
            "Error: config.json must include ad_tracking.doc_id and ad_tracking.api_key"
        )
        sys.exit(1)

    # Create client
    client = GristClient(DOC_ID, API_KEY, SERVER)

    # Ensure outputs directory exists
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("STEP 1: Exporting Grist database to JSON")
    print("=" * 80)

    # Export everything including attachments
    save_export(
        client,
        output_file="outputs/performance_data.json",
        download_attachments=not args.no_attachments,
        attachments_dir="outputs/attachments",
        manifest_file="outputs/attachments_manifest.json",
        attachments_tar="outputs/attachments.tar",
    )

    print("\n" + "=" * 80)
    print("STEP 2: Converting JSON to structured data files")
    print("=" * 80)

    # Generate structured files
    export_structured(
        json_path="outputs/performance_data.json",
        output_dir="outputs",
        format=args.format,
    )

    print("\n" + "=" * 80)
    print("✅ EXPORT COMPLETE!")
    print("=" * 80)
    print("Files generated:")
    print("  • outputs/performance_data.json (full database dump)")

    # Show generated files based on format
    file_ext = (
        "csv"
        if args.format == "csv"
        else "parquet" if args.format == "parquet" else "csv & parquet"
    )
    print(
        f"  • outputs/ad_weekly_performance.{args.format if args.format != 'both' else '{csv,parquet}'}"
    )
    print(
        f"  • outputs/ad_run_summary.{args.format if args.format != 'both' else '{csv,parquet}'}"
    )
    print(
        f"  • outputs/ad_lifetime_summary.{args.format if args.format != 'both' else '{csv,parquet}'}"
    )
    print(
        f"  • outputs/ad_components.{args.format if args.format != 'both' else '{csv,parquet}'}"
    )
    print(
        f"  • outputs/component_tags.{args.format if args.format != 'both' else '{csv,parquet}'}"
    )

    if not args.no_attachments:
        print("  • outputs/attachments/ (media files)")
        print("  • outputs/attachments_manifest.json")
        print("  • outputs/attachments.tar")


if __name__ == "__main__":
    main()

import json
import os
import tarfile
import shutil
import argparse
from typing import Dict, Any
from pathlib import Path

from grist.grist import GristClient


def create_tarball(source_dir: str, tar_path: str) -> str:
    """Create a tarball of the given directory."""
    source_dir = str(Path(source_dir))
    tar_path = str(Path(tar_path))

    suffixes = Path(tar_path).suffixes
    if tuple(suffixes) not in {(".tar",), (".gz",), (".tgz",), (".tar", ".gz")}:
        print(f"⚠️  Unusual archive extension: {tar_path}")

    gzip = suffixes[-2:] == [".tar", ".gz"] or suffixes[-1:] == [".tgz"]
    mode = "w:gz" if gzip else "w"

    with tarfile.open(tar_path, mode) as tf:
        tf.add(source_dir, arcname=os.path.basename(source_dir))

    return tar_path


def fetch_full_database_dump(
    client: GristClient,
    download_attachments: bool = True,
    attachments_dir: str = "attachments",
) -> Dict[str, Any]:
    """
    Scrape all tables, columns, records, and optionally attachments from Grist.
    Returns a unified dictionary representing the database.
    """
    database = {"doc_id": client.doc_id, "tables": {}, "attachments": {}}

    # Clear attachments directory if downloading attachments
    if download_attachments:
        att_path = Path(attachments_dir)
        if att_path.exists():
            print(f"Clearing existing attachments directory: {attachments_dir}")
            shutil.rmtree(att_path)

    tables = client.get_tables()
    print(f"Found {len(tables)} tables\n")

    for table in tables:
        table_id = table["id"]
        print(f"Processing table: {table_id}")

        columns = client.get_table_columns(table_id)
        records = client.fetch_records(table_id)

        database["tables"][table_id] = {
            "metadata": table,
            "columns": columns,
            "records": records,
            "record_count": len(records),
        }

        print(f"  - {len(columns)} columns")
        print(f"  - {len(records)} records")

        formula_cols = [c for c in columns if c.get("fields", {}).get("formula")]
        if formula_cols:
            print(f"  - {len(formula_cols)} formula columns:")
            for col in formula_cols:
                f = col.get("fields", {}).get("formula", "")
                print(f"    • {col['id']}: {f[:60]}...")

        if download_attachments:
            # Create table-specific subdirectory for attachments
            table_attachments_dir = os.path.join(attachments_dir, table_id)
            att_map = client.extract_attachments_from_records(
                table_id=table_id,
                records=records,
                columns=columns,
                output_dir=table_attachments_dir,
                name_field="Name",
                variant_field="Variant",
            )
            if att_map:
                database["attachments"].update(att_map)

        print()

    if database["attachments"]:
        print(f"Total attachments downloaded: {len(database['attachments'])}")

    return database


def save_export(
    client: GristClient,
    output_file: str = "performance_data.json",
    download_attachments: bool = True,
    attachments_dir: str = "attachments",
    manifest_file: str = "attachments_manifest.json",
    attachments_tar: str = "attachments.tar",
):
    print("Starting extraction.\n")
    data = fetch_full_database_dump(client, download_attachments, attachments_dir)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Successfully exported to {output_file}")

    if download_attachments and data.get("attachments"):
        manifest = {
            "doc_id": client.doc_id,
            "attachments_dir": attachments_dir,
            "count": len(data["attachments"]),
            "items": list(data["attachments"].values()),
        }
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"✓ Wrote manifest to {manifest_file}")

        tar_path = create_tarball(attachments_dir, attachments_tar)
        print(f"✓ Wrote tarball to {tar_path}")


# Example usage:
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Grist data")
    parser.add_argument(
        "--no-attachments", action="store_true", help="Skip downloading attachments"
    )
    args = parser.parse_args()

    # Load configuration from config.json
    config_file = "config.json"

    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found!")
        print(
            "Please copy config.example.json to config.json and add your credentials."
        )
        exit(1)

    with open(config_file, "r") as f:
        config = json.load(f)

    # Read from ad_tracking section
    ad_config = config.get("ad_tracking", {})
    DOC_ID = ad_config.get("doc_id")
    API_KEY = ad_config.get("api_key")
    SERVER = ad_config.get("server", "https://docs.getgrist.com")

    if not DOC_ID or not API_KEY:
        print(
            "Error: config.json must include ad_tracking.doc_id and ad_tracking.api_key"
        )
        exit(1)

    # Create client
    client = GristClient(DOC_ID, API_KEY, SERVER)

    # Ensure outputs directory exists
    os.makedirs("outputs", exist_ok=True)

    # Export everything including attachments
    save_export(
        client,
        output_file="outputs/performance_data.json",
        download_attachments=not args.no_attachments,
        attachments_dir="outputs/attachments",
        manifest_file="outputs/attachments_manifest.json",
        attachments_tar="outputs/attachments.tar",
    )
    # The JSON file will contain attachment references
    # The actual files will be in the "outputs/attachments" folder

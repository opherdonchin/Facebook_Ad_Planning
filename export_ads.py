import requests
import json
import os
import re
import tarfile
import mimetypes
import hashlib
import shutil
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path


class GristExtractor:
    def __init__(
        self, doc_id: str, api_key: str, server: str = "https://docs.getgrist.com"
    ):
        self.doc_id = doc_id
        self.api_key = api_key
        self.server = server
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def get_tables(self) -> List[Dict[str, Any]]:
        url = f"{self.server}/api/docs/{self.doc_id}/tables"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()["tables"]

    def get_table_columns(self, table_id: str) -> List[Dict[str, Any]]:
        url = f"{self.server}/api/docs/{self.doc_id}/tables/{table_id}/columns"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()["columns"]

    def get_table_data(self, table_id: str) -> List[Dict[str, Any]]:
        url = f"{self.server}/api/docs/{self.doc_id}/tables/{table_id}/records"
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()
        return r.json()["records"]

    def _sanitize_stem(self, s: str) -> str:
        s = (s or "").strip()
        s = re.sub(r"\s+", " ", s)
        s = s.replace("/", "-").replace("\\", "-")
        s = re.sub(r"[^A-Za-z0-9._ -]+", "_", s)
        s = s.strip(" ._-")
        return s or "unnamed"

    def _pick_extension(
        self, content_type: Optional[str], original_filename: Optional[str]
    ) -> str:
        # Prefer original extension if present (even if we ignore the original name).
        if original_filename:
            ext = Path(original_filename).suffix
            if ext:
                return ext.lower()

        if content_type:
            ct = content_type.split(";")[0].strip().lower()
            ext = mimetypes.guess_extension(ct)
            if ext:
                return ext.lower()

        return ""  # last resort: no extension

    def _unique_path(self, output_dir: str, stem: str, ext: str) -> str:
        p = Path(output_dir)
        p.mkdir(parents=True, exist_ok=True)

        base = p / f"{stem}{ext}"
        if not base.exists():
            return str(base)

        k = 2
        while True:
            candidate = p / f"{stem}__{k}{ext}"
            if not candidate.exists():
                return str(candidate)
            k += 1

    def _sha256(self, filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def download_attachment(
        self,
        attachment_id: str,
        output_dir: str = "attachments",
        desired_stem: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Download a single attachment, saving it as desired_stem + inferred extension.
        Returns a dict with filepath, original filename (if present), and sha256.
        """
        url = (
            f"{self.server}/api/docs/{self.doc_id}/attachments/{attachment_id}/download"
        )
        r = requests.get(url, headers=self.headers)
        r.raise_for_status()

        original_filename = None
        if "Content-Disposition" in r.headers:
            cd = r.headers["Content-Disposition"]
            if "filename=" in cd:
                original_filename = cd.split("filename=")[1].strip().strip('"')

        ext = self._pick_extension(r.headers.get("Content-Type"), original_filename)
        stem = self._sanitize_stem(desired_stem or f"attachment_{attachment_id}")
        filepath = self._unique_path(output_dir, stem, ext)

        with open(filepath, "wb") as f:
            f.write(r.content)

        return {
            "attachment_id": attachment_id,
            "filepath": filepath,
            "saved_filename": os.path.basename(filepath),
            "original_filename": original_filename,
            "content_type": r.headers.get("Content-Type"),
            "sha256": self._sha256(filepath),
        }

    def extract_attachments_from_records(
        self,
        table_id: str,
        records: List[Dict],
        columns: List[Dict],
        output_dir: str = "attachments",
        name_field: str = "Name",
        variant_field: str = "Variant",
    ) -> Dict[str, Dict[str, Any]]:
        """
        Download all attachments in this table, naming them using {Name} + {Variant}.
        Returns mapping: attachment_id -> metadata dict.
        """
        attachment_cols = [
            col
            for col in columns
            if col.get("fields", {}).get("type") in ["Attachments", "Attachment"]
        ]
        if not attachment_cols:
            return {}

        col_ids = [c["id"] for c in attachment_cols]
        print(f"  Found {len(attachment_cols)} attachment column(s): {col_ids}")

        attachment_map: Dict[str, Dict[str, Any]] = {}

        for record in records:
            fields = record.get("fields", {})
            rec_id = record.get("id")

            name = fields.get(name_field, "") or ""
            variant = fields.get(variant_field, "") or ""
            variant = variant.strip()

            base_stem = name.strip() or f"{table_id}_record_{rec_id}"
            if variant:
                base_stem = f"{base_stem}__{variant}"

            for col in attachment_cols:
                col_id = col["id"]
                attachments = fields.get(col_id, [])

                if not attachments or not isinstance(attachments, list):
                    continue

                # Filter to only valid numeric attachment IDs
                valid_attachments = [
                    str(a) for a in attachments if a and str(a).isdigit()
                ]

                if not valid_attachments:
                    continue

                # If a record has multiple files in the attachment cell, suffix them deterministically.
                for idx, att_id_str in enumerate(valid_attachments, start=1):
                    if att_id_str in attachment_map:
                        continue

                    stem = (
                        base_stem
                        if len(valid_attachments) == 1
                        else f"{base_stem}__{idx}"
                    )
                    try:
                        info = self.download_attachment(
                            att_id_str, output_dir, desired_stem=stem
                        )
                        info.update(
                            {
                                "table_id": table_id,
                                "record_id": rec_id,
                                "attachment_col": col_id,
                                "name": name,
                                "variant": variant,
                            }
                        )
                        attachment_map[att_id_str] = info
                        print(f"    ✓ Downloaded: {info['saved_filename']}")
                    except Exception as e:
                        print(f"    ✗ Failed to download attachment {att_id_str}: {e}")

        return attachment_map

    def _tar_attachments(self, attachments_dir: str, tar_path: str) -> str:
        attachments_dir = str(Path(attachments_dir))
        tar_path = str(Path(tar_path))

        suffixes = Path(tar_path).suffixes
        if tuple(suffixes) not in {(".tar",), (".gz",), (".tgz",), (".tar", ".gz")}:
            print(f"⚠️  Unusual archive extension: {tar_path}")

        gzip = suffixes[-2:] == [".tar", ".gz"] or suffixes[-1:] == [".tgz"]

        mode = "w:gz" if gzip else "w"

        with tarfile.open(tar_path, mode) as tf:
            tf.add(attachments_dir, arcname=os.path.basename(attachments_dir))

        return tar_path

    def extract_full_database(
        self,
        download_attachments: bool = True,
        attachments_dir: str = "attachments",
    ) -> Dict[str, Any]:
        database = {"doc_id": self.doc_id, "tables": {}, "attachments": {}}

        # Clear attachments directory if downloading attachments
        if download_attachments:
            att_path = Path(attachments_dir)
            if att_path.exists():
                print(f"Clearing existing attachments directory: {attachments_dir}")
                shutil.rmtree(att_path)

        tables = self.get_tables()
        print(f"Found {len(tables)} tables\n")

        for table in tables:
            table_id = table["id"]
            print(f"Processing table: {table_id}")

            columns = self.get_table_columns(table_id)
            records = self.get_table_data(table_id)

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
                att_map = self.extract_attachments_from_records(
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

    def save_to_json(
        self,
        output_file: str = "performance_data.json",
        download_attachments: bool = True,
        attachments_dir: str = "attachments",
        manifest_file: str = "attachments_manifest.json",
        attachments_tar: str = "attachments.tar",
    ):
        print("Starting extraction.\n")
        data = self.extract_full_database(download_attachments, attachments_dir)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Successfully exported to {output_file}")

        if download_attachments and data.get("attachments"):
            manifest = {
                "doc_id": self.doc_id,
                "attachments_dir": attachments_dir,
                "count": len(data["attachments"]),
                "items": list(data["attachments"].values()),
            }
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            print(f"✓ Wrote manifest to {manifest_file}")

            tar_path = self._tar_attachments(attachments_dir, attachments_tar)
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

    # Create extractor and export
    extractor = GristExtractor(DOC_ID, API_KEY, SERVER)

    # Export everything including attachments
    data = extractor.save_to_json(
        output_file="performance_data.json",
        download_attachments=not args.no_attachments,
        attachments_dir="attachments",
        manifest_file="attachments_manifest.json",
        attachments_tar="attachments.tar",
    )
    # The JSON file will contain attachment references
    # The actual files will be in the "attachments" folder

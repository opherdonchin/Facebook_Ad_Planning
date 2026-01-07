import requests
import json
import os
import re
import mimetypes
import hashlib
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path


class GristClient:
    def __init__(
        self, doc_id: str, api_key: str, server: str = "https://docs.getgrist.com"
    ):
        self.doc_id = doc_id
        self.api_key = api_key
        self.server = server.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _url(self, path: str) -> str:
        # Some methods used /api/docs/... and some used /api/docs/...
        # I'll standardize on /api/docs/{doc_id}{path}
        # But wait, get_tables uses /api/docs/{doc_id}/tables
        # fetch_records uses /api/docs/{doc_id}/tables/{table_id}/records
        return f"{self.server}/api/docs/{self.doc_id}{path}"

    def get_tables(self) -> List[Dict[str, Any]]:
        url = self._url("/tables")
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()["tables"]

    def get_table_columns(self, table_id: str) -> List[Dict[str, Any]]:
        url = self._url(f"/tables/{table_id}/columns")
        r = self.session.get(url)
        r.raise_for_status()
        return r.json()["columns"]

    def fetch_records(self, table_id: str) -> List[Dict[str, Any]]:
        url = self._url(f"/tables/{table_id}/records")
        r = self.session.get(url, timeout=60)
        r.raise_for_status()
        return r.json().get("records", [])

    def add_records(self, table_id: str, records: List[Dict[str, Any]]) -> List[int]:
        url = self._url(f"/tables/{table_id}/records")
        payload = {"records": records}
        r = self.session.post(url, json=payload, timeout=60)
        if not r.ok:
            print(f"[ERROR] Failed to add records. Status: {r.status_code}")
            print(f"[ERROR] Response: {r.text}")
            print(
                f"[ERROR] Sample record being sent: {records[0] if records else 'None'}"
            )
        r.raise_for_status()
        out = r.json().get("records", [])
        return [x.get("id") for x in out if "id" in x]

    def patch_records(self, table_id: str, records: List[Dict[str, Any]]) -> None:
        if not records:
            return
        url = self._url(f"/tables/{table_id}/records")
        payload = {"records": records}
        r = self.session.patch(url, json=payload, timeout=60)
        if not r.ok:
            print(f"[ERROR] Failed to patch records. Status: {r.status_code}")
            print(f"[ERROR] Response: {r.text}")
            print(
                f"[ERROR] Sample record being sent: {records[0] if records else 'None'}"
            )
        r.raise_for_status()

    # ----------------------------------------------------------------------
    # Attachment Helpers
    # ----------------------------------------------------------------------

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
        if original_filename:
            ext = Path(original_filename).suffix
            if ext:
                return ext.lower()

        if content_type:
            ct = content_type.split(";")[0].strip().lower()
            ext = mimetypes.guess_extension(ct)
            if ext:
                return ext.lower()

        return ""

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
        url = (
            f"{self.server}/api/docs/{self.doc_id}/attachments/{attachment_id}/download"
        )
        r = self.session.get(url)
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

                valid_attachments = [
                    str(a) for a in attachments if a and str(a).isdigit()
                ]

                if not valid_attachments:
                    continue

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

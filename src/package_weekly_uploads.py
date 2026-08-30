"""Package weekly planning files into upload-ready zip bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class BundleFile:
    source: Path
    arcname: str


@dataclass(frozen=True)
class Bundle:
    zip_name: str
    description: str
    files: tuple[BundleFile, ...]


STRUCTURED_DATA_FILES = (
    "ad_weekly_performance.csv",
    "ad_run_summary.csv",
    "ad_lifetime_summary.csv",
    "ad_components.csv",
    "component_media_lifetime.csv",
    "component_headline_lifetime.csv",
    "component_text_lifetime.csv",
    "component_tags.csv",
)

PROJECT_CONTEXT_FILES = (
    "documents/decision_log.md",
    "documents/data_schema.md",
    "documents/decision_log_format.md",
    "documents/decision_metrics.md",
    "documents/PROJECT_GUIDE.md",
    "documents/tag_taxonomy.md",
    "documents/decision_heuristics.md",
    "documents/weekly_prompt.md",
)

MANIFEST_NAME = "weekly_upload_manifest.json"


def build_bundles(repo_root: Path, outputs_dir: Path) -> tuple[Bundle, ...]:
    data_files = (
        BundleFile(outputs_dir / "performance_data.json", "data/performance_data.json"),
        *(
            BundleFile(outputs_dir / filename, f"data/structured/{filename}")
            for filename in STRUCTURED_DATA_FILES
        ),
    )

    asset_files = (
        BundleFile(
            outputs_dir / "attachments_manifest.json",
            "assets/attachments_manifest.json",
        ),
        BundleFile(outputs_dir / "attachments.tar", "assets/attachments.tar"),
    )

    context_files = tuple(
        BundleFile(repo_root / filename, f"context/{filename}")
        for filename in PROJECT_CONTEXT_FILES
    )

    return (
        Bundle(
            zip_name="weekly_upload_data.zip",
            description="Structured weekly data tables and raw Grist JSON export.",
            files=data_files,
        ),
        Bundle(
            zip_name="weekly_upload_assets.zip",
            description="Creative asset manifest and attachment archive.",
            files=asset_files,
        ),
        Bundle(
            zip_name="weekly_upload_context.zip",
            description="Decision log, schema, prompt, and planning reference documents.",
            files=context_files,
        ),
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def validate_files(bundles: tuple[Bundle, ...]) -> list[Path]:
    missing = []
    for bundle in bundles:
        for bundle_file in bundle.files:
            if not bundle_file.source.is_file():
                missing.append(bundle_file.source)
    return missing


def build_manifest(bundles: tuple[Bundle, ...], repo_root: Path) -> dict:
    manifest_bundles = []

    for bundle in bundles:
        files = []
        for bundle_file in bundle.files:
            source = bundle_file.source
            files.append(
                {
                    "source": display_path(source, repo_root),
                    "archive_path": bundle_file.arcname,
                    "size_bytes": source.stat().st_size,
                    "sha256": sha256_file(source),
                }
            )

        manifest_bundles.append(
            {
                "zip_name": bundle.zip_name,
                "description": bundle.description,
                "files": files,
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
        "purpose": "Weekly AI planning upload bundles for Facebook ad planning.",
        "upload_instruction": "Upload all zip files in one batch before analysis.",
        "bundles": manifest_bundles,
    }


def compression_for(path: Path) -> int:
    if path.suffix.lower() in {".zip", ".tar", ".gz", ".tgz", ".mp4", ".mov"}:
        return zipfile.ZIP_STORED
    return zipfile.ZIP_DEFLATED


def write_bundle(bundle: Bundle, destination: Path, manifest_path: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_handle = tempfile.NamedTemporaryFile(
        delete=False,
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temp_path = Path(temp_handle.name)
    temp_handle.close()

    try:
        with zipfile.ZipFile(temp_path, mode="w") as archive:
            for bundle_file in bundle.files:
                archive.write(
                    bundle_file.source,
                    bundle_file.arcname,
                    compress_type=compression_for(bundle_file.source),
                )
            archive.write(
                manifest_path,
                f"manifest/{MANIFEST_NAME}",
                compress_type=zipfile.ZIP_DEFLATED,
            )
        temp_path.replace(destination)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create weekly upload zip bundles in the outputs directory."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--outputs-dir",
        default="outputs",
        help="Directory containing exported data and receiving zip bundles.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate required files and print planned bundles without writing zips.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    outputs_dir = (repo_root / args.outputs_dir).resolve()
    outputs_dir.mkdir(parents=True, exist_ok=True)

    bundles = build_bundles(repo_root, outputs_dir)
    missing = validate_files(bundles)
    if missing:
        print("Missing required files; weekly upload bundles were not created.")
        for path in missing:
            print(f"  - {path}")
        print("\nRun the weekly export pipeline first, then retry:")
        print("  pixi run export_ads")
        print("  pixi run package_uploads")
        return 1

    print("Weekly upload bundles:")
    for bundle in bundles:
        print(f"  - outputs/{bundle.zip_name}")
        for bundle_file in bundle.files:
            print(f"      {bundle_file.arcname}")

    if args.dry_run:
        print("\nDry run complete. No files were written.")
        return 0

    manifest = build_manifest(bundles, repo_root)
    manifest_path = outputs_dir / MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    for bundle in bundles:
        destination = outputs_dir / bundle.zip_name
        write_bundle(bundle, destination, manifest_path)
        print(f"Created {destination}")

    print(f"Created {manifest_path}")
    print("\nUpload these three zip files together:")
    for bundle in bundles:
        print(f"  - outputs/{bundle.zip_name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Refresh a local Grist export from a successfully written Meta snapshot.

This is a quota-exhaustion fallback for the weekly workflow. It patches only
the already-synced Weekly_runs rows represented by a captured snapshot, then
rebuilds the advertising-derived tables locally with the same production
transform functions. It never writes to Grist.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ibis
import pandas as pd

from export_structured_data import main as export_structured
from transforms import TRANSFORMS


REFRESH_TRANSFORMS = (
    "weekly_metrics_prod",
    "lifetime_ad_metrics_prod",
    "last_contiguous_run_ad_metrics_prod",
    "tag_lifetime_rollups_prod",
    "component_media_lifetime_metrics_prod",
    "component_headline_lifetime_metrics_prod",
    "component_text_lifetime_metrics_prod",
    "component_tags_prod",
)


def require_passed_snapshot(snapshot: dict[str, Any]) -> None:
    """Reject unvalidated snapshots before they can modify local exports."""
    status = str(snapshot.get("validation_status") or "").strip().lower()
    if status != "passed":
        raise ValueError(
            "Snapshot validation_status must be 'passed' before refresh. "
            f"Found {status or 'missing'!r}."
        )


def flatten_table(data: dict[str, Any], table_id: str) -> pd.DataFrame:
    records = data["tables"][table_id]["records"]
    rows = []
    for record in records:
        row = {"id": record["id"]}
        row.update(record.get("fields", {}))
        rows.append(row)
    return pd.DataFrame(rows)


def prepare_table(
    data: dict[str, Any], table_id: str, mapping: dict[str, str]
) -> pd.DataFrame:
    frame = flatten_table(data, table_id).infer_objects()
    missing = set(mapping) - set(frame.columns)
    if missing:
        raise ValueError(f"{table_id} is missing expected columns: {sorted(missing)}")
    frame = frame[list(mapping)].rename(columns=mapping).infer_objects()

    # Match the production runner's object normalization so local results have
    # the same join-key behavior as a normal Grist transform run.
    for column in frame.select_dtypes(include=["object"]).columns:
        sample = frame[column].dropna()
        if sample.empty:
            frame[column] = frame[column].astype(str)
            continue
        values = sample.head(min(100, len(sample))).tolist()
        int_flags = [isinstance(value, int) and not isinstance(value, bool) for value in values]
        if all(int_flags):
            frame[column] = frame[column].astype("int64")
        elif sum(int_flags) / len(int_flags) > 0.8:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
        else:
            frame[column] = frame[column].astype(str)
    return frame


def json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def replace_derived_table(data: dict[str, Any], table_id: str, frame: pd.DataFrame) -> None:
    if "id" in frame.columns:
        frame = frame.drop(columns=["id"])
    records = []
    for record_id, row in enumerate(frame.to_dict(orient="records"), start=1):
        records.append(
            {
                "id": record_id,
                "fields": {key: json_value(value) for key, value in row.items()},
            }
        )
    table = data["tables"][table_id]
    table["records"] = records
    table["record_count"] = len(records)


def patch_weekly_runs(data: dict[str, Any], snapshot: dict[str, Any]) -> None:
    ads_by_name = {
        record["fields"].get("Name"): record["id"]
        for record in data["tables"]["Ads"]["records"]
    }
    desired = {row["ad_name"]: row for row in snapshot["rows"]}
    unknown = set(desired) - set(ads_by_name)
    if unknown:
        raise ValueError(f"Snapshot ads are absent from the export: {sorted(unknown)}")

    week = snapshot["week"]
    found: set[str] = set()
    for record in data["tables"]["Weekly_runs"]["records"]:
        fields = record["fields"]
        if fields.get("A") != week:
            continue
        ad_name = next(
            (name for name, ad_id in ads_by_name.items() if ad_id == fields.get("Ad")),
            None,
        )
        if ad_name not in desired:
            continue
        row = desired[ad_name]
        fields["Spend"] = row["spend"]
        fields["Leads"] = row["leads"]
        fields["Intended_run"] = row["intended_run"]
        fields["CPL"] = row["spend"] / row["leads"] if row["leads"] else None
        fields["Performing"] = bool(
            row["leads"] and fields["CPL"] is not None and fields["CPL"] <= 50
        )
        found.add(ad_name)

    missing = set(desired) - found
    if missing:
        raise ValueError(f"Snapshot rows were not found in Weekly_runs: {sorted(missing)}")


def patch_ads_rollups(data: dict[str, Any], snapshot: dict[str, Any]) -> None:
    patches = {row["ad_name"]: row for row in snapshot.get("ads_patches", [])}
    if not patches:
        return
    found: set[str] = set()
    for record in data["tables"]["Ads"]["records"]:
        fields = record["fields"]
        ad_name = fields.get("Name")
        if ad_name not in patches:
            continue
        patch = patches[ad_name]
        fields.update(
            {
                "Total_leads": patch["total_leads"],
                "Trial_lessons": patch["trial_lessons"],
                "Registered": patch["registered"],
                "Failed": patch["failed"],
            }
        )
        found.add(ad_name)
    missing = set(patches) - found
    if missing:
        raise ValueError(f"Ads rollup patches did not match export rows: {sorted(missing)}")


def rebuild_derived_tables(data: dict[str, Any]) -> None:
    for transform_name in REFRESH_TRANSFORMS:
        spec = TRANSFORMS[transform_name]
        connection = ibis.duckdb.connect()
        tables = {}
        for alias, table_id in spec.input_tables.items():
            mapping = spec.select_rename[alias]
            frame = prepare_table(data, table_id, mapping)
            tables[alias] = connection.create_table(alias, frame)
        result = spec.transform(tables)
        replace_derived_table(data, spec.output_table, result)
        print(f"Rebuilt {spec.output_table}: {len(result)} rows")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--json", type=Path, default=Path("outputs/performance_data.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = json.loads(args.json.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))

    require_passed_snapshot(snapshot)
    patch_weekly_runs(data, snapshot)
    patch_ads_rollups(data, snapshot)
    rebuild_derived_tables(data)
    data["offline_refresh"] = {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_snapshot": str(args.snapshot),
        "reason": "Grist monthly API allowance was exhausted after the Meta rows were written.",
        "scope": "Weekly_runs snapshot, reconciled Ads rollup patches, and advertising-derived tables; no Grist write.",
        "known_stale_table": "Derived_Lifetime_Ad_Conversions could not be regenerated without a fresh Leads API read; use the reconciled Ads rollups and the reconciliation report instead.",
    }
    args.json.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    export_structured(str(args.json), str(args.output_dir), "csv")
    print(f"Refreshed {args.json} and structured CSVs from {args.snapshot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

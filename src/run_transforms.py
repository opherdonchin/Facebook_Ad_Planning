"""
Generic runner for Grist table → table transforms using DuckDB + Ibis.

Responsibilities:
- Fetch input tables from Grist
- Materialize them into DuckDB
- Expose them as Ibis tables
- Run a user-provided transform
- Write results back to Grist

No business logic lives here.
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, List

import duckdb
import ibis
import pandas as pd

from grist import GristClient


# -------------------------
# Types
# -------------------------

TransformFn = Callable[[Dict[str, ibis.expr.types.Table]], pd.DataFrame]


# -------------------------
# Core runner
# -------------------------


def infer_grist_type(series: pd.Series, col_name: str) -> str:
    """Guess Grist column type from pandas series."""
    if series.empty:
        return "Text"

    dtype = str(series.dtype)

    if pd.api.types.is_float_dtype(series):
        if "CPL" in col_name or "Spend" in col_name:
            return "Numeric"
        return "Numeric"

    if pd.api.types.is_integer_dtype(series):
        # Heuristic: if column name suggests date/time and values are large, maybe DateTime?
        if "Week" in col_name and series.mean() > 1000000000:
            return "DateTime"
        return "Int"

    if pd.api.types.is_bool_dtype(series):
        return "Bool"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "DateTime"

    return "Text"


def sync_schema(client: GristClient, table_id: str, df: pd.DataFrame) -> None:
    """Ensure Grist table has columns matching the DataFrame types."""
    # Get existing columns
    try:
        existing_cols = client.get_table_columns(table_id)
        existing_ids = {c["id"] for c in existing_cols}
    except Exception as e:
        print(f"Warning: Could not fetch schema for {table_id}: {e}")
        existing_ids = set()

    to_create = []
    to_update = []

    for col in df.columns:
        grist_type = infer_grist_type(df[col], col)

        col_def = {"id": col, "fields": {"type": grist_type}}

        if col in existing_ids:
            to_update.append(col_def)
        else:
            col_def["fields"]["label"] = col
            to_create.append(col_def)

    if to_create:
        print(f"Creating columns in {table_id}: {[c['id'] for c in to_create]}")
        client.create_columns(table_id, to_create)

    if to_update:
        print(f"Updating columns in {table_id}: {[c['id'] for c in to_update]}")
        client.update_columns(table_id, to_update)


def run_transform(
    *,
    input_client: GristClient,
    input_tables: Dict[str, str],
    output_client: GristClient,
    output_table: str,
    transform: TransformFn,
    overwrite: bool = True,
    select_rename: Dict[str, Dict[str, str]] = None,
) -> None:
    """
    Run a table-level transform.

    Parameters
    ----------
    input_client :
        Grist client to read input tables from
    input_tables :
        Mapping alias -> grist_table_id
        Example: {"ads": "Ads", "performance": "Ad_Performance"}
    output_client :
        Grist client to write results to
    output_table :
        Target Grist table ID
    transform :
        Function taking dict(alias -> ibis table) and returning a pandas DataFrame
    overwrite :
        If True, deletes all rows in output table before inserting
    select_rename :
        Optional mapping of alias -> {raw_col: canonical_col}.
        If provided, only these columns are selected and renamed before the transform sees them.
    """

    # 1. Fetch input tables from Grist
    raw_tables: Dict[str, List[dict]] = {}
    for alias, table_id in input_tables.items():
        # Fetch directly as flat dicts suitable for DuckDB/Pandas
        records = input_client.fetch_records(table_id, flat=True)
        raw_tables[alias] = records

    # 2. Load into DuckDB
    # con = duckdb.connect(database=":memory:")
    ibis_con = ibis.duckdb.connect()

    ibis_tables: Dict[str, ibis.expr.types.Table] = {}

    for alias, records in raw_tables.items():
        df = pd.DataFrame(records)

        # 2b. Apply select_rename immediately if configured
        # This prevents loading unused/complex columns (like Reference Lists) into DuckDB/Ibis
        if select_rename and alias in select_rename:
            mapping = select_rename[alias]
            # Verify columns exist before selecting
            available_cols = set(df.columns)
            missing_cols = set(mapping.keys()) - available_cols
            if missing_cols:
                print(
                    f"Warning: Columns {missing_cols} expected for alias '{alias}' but not found in data."
                )

            # Select only keys that exist
            valid_keys = [k for k in mapping.keys() if k in available_cols]
            df = df[valid_keys].rename(columns=mapping)

        # con.register(alias, df)
        # ibis_tables[alias] = ibis_con.table(alias)
        ibis_tables[alias] = ibis_con.create_table(alias, df)

    # Validate alias contract: transform must reference existing keys
    # (we can’t introspect the transform reliably, so we just make the error clearer)
    if not ibis_tables:
        raise ValueError("No input tables were provided.")

    # Optional: enforce non-empty aliases
    for k in ibis_tables.keys():
        if not k or not isinstance(k, str):
            raise ValueError(f"Invalid table alias: {k!r}")

    # 3. Run transform (pure logic)
    print("Running transform logic...")
    result_df = transform(ibis_tables)
    print(f"Transform produced {len(result_df)} rows.")

    if not isinstance(result_df, pd.DataFrame):
        raise TypeError("Transform must return a pandas DataFrame")

    # Drop 'id' column if it exists, as it's system-managed in Grist
    if "id" in result_df.columns:
        result_df = result_df.drop(columns=["id"])

    # 4. Write back to Grist

    # Check if table exists
    existing_tables = [t["id"] for t in output_client.get_tables()]

    if output_table not in existing_tables:
        print(f"Creating new table with typed schema: {output_table}")
        columns_spec = []
        for col in result_df.columns:
            g_type = infer_grist_type(result_df[col], col)
            columns_spec.append({"id": col, "fields": {"type": g_type, "label": col}})
        output_client.create_table(output_table, columns_spec)

    else:
        # Table exists, ensure columns match types
        print(f"Syncing schema for existing table: {output_table}")
        sync_schema(output_client, output_table, result_df)

        if overwrite:
            print(f"Overwriting table: {output_table}")
            output_client.delete_all_records(output_table)

    # Wrap for Grist API: {col: val} -> {"fields": {col: val}}
    # Convert NaNs to None for JSON compliance
    output_records = []
    for r in result_df.to_dict(orient="records"):
        clean_r = {}
        for k, v in r.items():
            # Check for NaN (v != v) and Inf
            if isinstance(v, float) and (
                v != v or v == float("inf") or v == float("-inf")
            ):
                clean_r[k] = None
            else:
                clean_r[k] = v
        output_records.append({"fields": clean_r})

    print(f"Prepared {len(output_records)} records to add.")
    if output_records:
        print(f"Sample: {output_records[0]}")

    output_client.add_records(
        output_table,
        output_records,
    )


if __name__ == "__main__":
    import argparse
    from utils import load_config
    from transforms import TRANSFORMS

    parser = argparse.ArgumentParser(description="Run Grist transforms.")
    parser.add_argument(
        "transform_names",
        nargs="+",
        help="Name(s) of the transform to run (defined in transforms.py)",
    )
    parser.add_argument(
        "--profile",
        default="test",
        help="Config profile to use (e.g., 'test', 'ad_tracking'). Defaults to 'test'.",
    )
    args = parser.parse_args()

    # Load config and initialize client ONCE
    config = load_config("config.json")
    profile_config = config.get(args.profile)

    if not profile_config:
        raise ValueError(f"Profile '{args.profile}' not found in config.json")

    doc_id = profile_config.get("doc_id")
    api_key = profile_config.get("api_key")
    server = profile_config.get("server", "https://docs.getgrist.com")

    if not doc_id or not api_key:
        raise ValueError(
            f"Config profile '{args.profile}' must include doc_id and api_key"
        )

    client = GristClient(doc_id=doc_id, api_key=api_key, server=server)

    # Run each requested transform
    for name in args.transform_names:
        spec = TRANSFORMS.get(name)
        if not spec:
            available = ", ".join(TRANSFORMS.keys())
            print(f"[ERROR] Unknown transform: '{name}'. Available: {available}")
            continue

        print(f"\n[{name}] Running transform (profile: {args.profile})...")

        # Allow config to override input table IDs (e.g. for different envs)
        # Registry has defaults (e.g. "perf" -> "Test_ad_performance")
        # Config can have "inputs": { "perf": "Weekly_runs" }
        input_tables = spec.input_tables.copy()
        config_inputs = profile_config.get("inputs", {})
        if config_inputs:
            input_tables.update(config_inputs)
            print(f"[{name}] Overriding input tables from config: {config_inputs}")

        try:
            run_transform(
                input_client=client,
                input_tables=input_tables,
                output_client=client,
                output_table=spec.output_table,
                transform=spec.transform,
                overwrite=spec.overwrite,
                select_rename=spec.select_rename,
            )
            print(f"[{name}] Completed successfully.")
        except Exception as e:
            print(f"[{name}] FAILED: {e}")
            import traceback

            traceback.print_exc()

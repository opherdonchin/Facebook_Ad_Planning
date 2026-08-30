"""Build a standalone artifact for evaluating decision-log outcomes.

The weekly planning bundles intentionally stay focused on making the next
decision. This package is for retrospective evaluation of the decision rules.
It derives the main performance tables from raw Grist tables in
performance_data.json so it does not depend on Grist derived tables being
fresh.
"""

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
from typing import Any

import pandas as pd

from export_ads import fetch_full_database_dump
from export_structured_data import extract_table_df, load_performance_data
from grist.grist import GristClient
from utils import load_config

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


CONTEXT_FILES = (
    "documents/decision_log.md",
    "documents/decision_log_format.md",
    "documents/decision_heuristics.md",
    "documents/decision_metrics.md",
    "documents/PROJECT_GUIDE.md",
    "documents/tag_taxonomy.md",
    "documents/weekly_prompt.md",
    "documents/data_schema.md",
)


@dataclass(frozen=True)
class ArtifactFile:
    source: Path
    arcname: str


def normalize_campaign(value: Any) -> Any:
    if pd.isna(value):
        return value

    text = str(value).strip()
    lowered = text.lower()

    if lowered in {"w", "women", "womens campaign", "women's campaign"}:
        return "W"
    if lowered in {"m", "men", "mens campaign", "men's campaign"}:
        return "M"

    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return text

    if numeric == 1:
        return "W"
    if numeric == 2:
        return "M"
    return text


def safe_numeric(series: pd.Series, dtype: str | None = None) -> pd.Series:
    out = pd.to_numeric(series, errors="coerce")
    if dtype:
        out = out.astype(dtype)
    return out


def table_or_empty(data: dict[str, Any], table_name: str) -> pd.DataFrame:
    if table_name not in data.get("tables", {}):
        return pd.DataFrame()
    return extract_table_df(data, table_name)


def build_ad_components(data: dict[str, Any]) -> pd.DataFrame:
    ads = table_or_empty(data, "Ads")
    creatives = table_or_empty(data, "Creatives")
    media = table_or_empty(data, "Media")
    headlines = table_or_empty(data, "Headlines")
    texts = table_or_empty(data, "Texts")

    columns = [
        "ad_id",
        "ad_name",
        "campaign",
        "media_id",
        "media_name",
        "media_variant",
        "media_format",
        "headline_id",
        "headline_text",
        "text_id",
        "text_name",
        "text_variant",
        "primary_text",
    ]

    if ads.empty:
        return pd.DataFrame(columns=columns)

    ads = ads.rename(
        columns={"id": "ad_id", "Name": "ad_name", "Creative": "creative_id", "Text": "text_id"}
    )
    for df, refs in (
        (ads, ("ad_id", "creative_id", "text_id")),
        (creatives, ("id", "Media", "Headline")),
        (media, ("id",)),
        (headlines, ("id",)),
        (texts, ("id",)),
    ):
        for ref in refs:
            if ref in df.columns:
                df[ref] = df[ref].astype("string")

    out = ads.loc[:, [c for c in ["ad_id", "ad_name", "Campaign", "creative_id", "text_id"] if c in ads.columns]]

    if not creatives.empty:
        out = out.merge(
            creatives.loc[:, [c for c in ["id", "Media", "Headline"] if c in creatives.columns]],
            left_on="creative_id",
            right_on="id",
            how="left",
            suffixes=("", "_creative"),
        )
        out = out.rename(columns={"Media": "media_id", "Headline": "headline_id"})

    if not media.empty and "media_id" in out.columns:
        out = out.merge(
            media.loc[:, [c for c in ["id", "Name", "Variant", "Format"] if c in media.columns]],
            left_on="media_id",
            right_on="id",
            how="left",
            suffixes=("", "_media"),
        )
        out = out.rename(
            columns={
                "Name": "media_name",
                "Variant": "media_variant",
                "Format": "media_format",
            }
        )

    if not headlines.empty and "headline_id" in out.columns:
        out = out.merge(
            headlines.loc[:, [c for c in ["id", "Text"] if c in headlines.columns]],
            left_on="headline_id",
            right_on="id",
            how="left",
            suffixes=("", "_headline"),
        )
        out = out.rename(columns={"Text": "headline_text"})

    if not texts.empty:
        out = out.merge(
            texts.loc[:, [c for c in ["id", "Name", "Variant", "Primary_text"] if c in texts.columns]],
            left_on="text_id",
            right_on="id",
            how="left",
            suffixes=("", "_text"),
        )
        out = out.rename(
            columns={
                "Name": "text_name",
                "Variant": "text_variant",
                "Primary_text": "primary_text",
            }
        )

    out["campaign"] = out["Campaign"].apply(normalize_campaign) if "Campaign" in out.columns else pd.NA

    for col in columns:
        if col not in out.columns:
            out[col] = pd.NA

    return out.loc[:, columns].sort_values(["campaign", "ad_name"], kind="stable")


def build_weekly_run_history(data: dict[str, Any]) -> pd.DataFrame:
    weekly = table_or_empty(data, "Weekly_runs")
    components = build_ad_components(data).loc[:, ["ad_id", "ad_name", "campaign"]]

    columns = [
        "weekly_run_id",
        "iso_week",
        "week_end_date",
        "week_complete",
        "campaign",
        "ad_id",
        "ad_name",
        "spend",
        "leads",
        "cpl",
        "intended_run",
    ]

    if weekly.empty:
        return pd.DataFrame(columns=columns)

    out = weekly.rename(
        columns={"id": "weekly_run_id", "A": "iso_week", "Ad": "ad_id", "Intended_run": "intended_run"}
    )
    out["ad_id"] = out["ad_id"].astype("string")
    components["ad_id"] = components["ad_id"].astype("string")
    out = out.merge(components, on="ad_id", how="left")

    out["spend"] = safe_numeric(out.get("Spend", pd.Series(dtype=float)))
    out["leads"] = safe_numeric(out.get("Leads", pd.Series(dtype=int)), "Int64")
    out["cpl"] = out["spend"] / out["leads"].where(out["leads"] > 0)
    out["intended_run"] = out.get("intended_run", False).fillna(False).astype(bool)
    out["week_end_date"] = pd.to_datetime(out.get("Week"), unit="s", utc=True, errors="coerce").dt.date
    out["week_complete"] = out["week_end_date"] <= datetime.now().date()

    for col in columns:
        if col not in out.columns:
            out[col] = pd.NA

    return out.loc[:, columns].sort_values(["week_end_date", "campaign", "ad_name"], kind="stable")


def build_ad_lifetime_summary(weekly: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "campaign",
        "ad_name",
        "lifetime_spend",
        "lifetime_leads",
        "lifetime_cpl",
        "first_seen_week",
        "last_seen_week",
        "weeks_active",
    ]
    if weekly.empty:
        return pd.DataFrame(columns=columns)

    g = weekly.groupby(["campaign", "ad_name"], dropna=False, as_index=False).agg(
        lifetime_spend=("spend", "sum"),
        lifetime_leads=("leads", "sum"),
        first_seen_week=("iso_week", "first"),
        last_seen_week=("iso_week", "last"),
        weeks_active=("iso_week", "nunique"),
    )
    g["lifetime_cpl"] = g["lifetime_spend"] / g["lifetime_leads"].where(g["lifetime_leads"] > 0)
    return g.loc[:, columns].sort_values(["campaign", "lifetime_cpl", "ad_name"], na_position="last")


def build_ad_last_run_summary(weekly: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "campaign",
        "ad_name",
        "run_start_week",
        "run_end_week",
        "weeks_in_run",
        "run_spend",
        "run_leads",
        "run_cpl",
    ]
    if weekly.empty:
        return pd.DataFrame(columns=columns)

    rows = []
    for (campaign, ad_name), group in weekly.groupby(["campaign", "ad_name"], dropna=False, sort=False):
        g = group.sort_values("week_end_date").reset_index(drop=True)
        gaps = pd.to_datetime(g["week_end_date"]).diff().dt.days
        block = (gaps.isna() | (gaps != 7)).cumsum()
        last = g[block == block.iloc[-1]]
        spend = float(last["spend"].sum())
        leads = int(last["leads"].fillna(0).sum())
        rows.append(
            {
                "campaign": campaign,
                "ad_name": ad_name,
                "run_start_week": last["iso_week"].iloc[0],
                "run_end_week": last["iso_week"].iloc[-1],
                "weeks_in_run": int(len(last)),
                "run_spend": spend,
                "run_leads": leads,
                "run_cpl": spend / leads if leads > 0 else pd.NA,
            }
        )
    return pd.DataFrame(rows, columns=columns).sort_values(["campaign", "ad_name"], kind="stable")


def build_ad_lifetime_conversions(data: dict[str, Any]) -> pd.DataFrame:
    df = table_or_empty(data, "Derived_Lifetime_Ad_Conversions")
    columns = [
        "campaign",
        "ad_name",
        "leads_attributed",
        "leads_with_trial",
        "trial_conversion_rate",
        "leads_registered",
        "registration_conversion_rate",
        "leads_failed",
        "failure_rate",
    ]
    if df.empty:
        return pd.DataFrame(columns=columns)

    out = pd.DataFrame(
        {
            "campaign": df.get("Campaign", pd.Series(dtype=str)).apply(normalize_campaign),
            "ad_name": df.get("Ad", pd.Series(dtype=str)),
            "leads_attributed": safe_numeric(df.get("Leads_Attributed", pd.Series(dtype=int)), "Int64"),
            "leads_with_trial": safe_numeric(df.get("Leads_With_Trial", pd.Series(dtype=int)), "Int64"),
            "trial_conversion_rate": safe_numeric(df.get("Trial_Conversion_Rate", pd.Series(dtype=float))),
            "leads_registered": safe_numeric(df.get("Leads_Registered", pd.Series(dtype=int)), "Int64"),
            "registration_conversion_rate": safe_numeric(df.get("Registration_Conversion_Rate", pd.Series(dtype=float))),
            "leads_failed": safe_numeric(df.get("Leads_Failed", pd.Series(dtype=int)), "Int64"),
            "failure_rate": safe_numeric(df.get("Failure_Rate", pd.Series(dtype=float))),
        }
    )
    return out.loc[:, columns].sort_values(["campaign", "ad_name"], kind="stable")


def build_component_lifetime(
    weekly: pd.DataFrame,
    components: pd.DataFrame,
    *,
    id_col: str,
    name_col: str,
    extra_cols: tuple[str, ...] = (),
) -> pd.DataFrame:
    join_cols = ["ad_id", id_col, name_col, *extra_cols]
    comp = components.loc[:, [c for c in join_cols if c in components.columns]]
    weekly_comp = weekly.merge(comp, on="ad_id", how="left")
    group_cols = [id_col, name_col, *extra_cols]
    out = weekly_comp.groupby(group_cols, dropna=False, as_index=False).agg(
        spend=("spend", "sum"),
        leads=("leads", "sum"),
        ads=("ad_id", "nunique"),
    )
    out["cpl"] = out["spend"] / out["leads"].where(out["leads"] > 0)
    return out.sort_values(["cpl", "spend"], ascending=[True, False], na_position="last")


def lookup_values(data: dict[str, Any], table_name: str, value_column: str) -> dict[str, Any]:
    df = table_or_empty(data, table_name)
    if df.empty or "id" not in df.columns or value_column not in df.columns:
        return {}
    return dict(zip(df["id"].astype("string"), df[value_column]))


def dereference(value: Any, lookup: dict[str, Any]) -> Any:
    if pd.isna(value):
        return pd.NA
    key = str(value)
    return lookup.get(key, value)


def build_component_tags(data: dict[str, Any]) -> pd.DataFrame:
    media = table_or_empty(data, "Media")
    headlines = table_or_empty(data, "Headlines")
    texts = table_or_empty(data, "Texts")

    lookups = {
        "Media_Style": lookup_values(data, "Media_Style", "Media_Style"),
        "Media_Energy": lookup_values(data, "Media_Energy", "Media_Energy"),
        "Tone": lookup_values(data, "Tone", "Tone"),
        "Promise": lookup_values(data, "Promise_types", "Promise"),
        "Hook": lookup_values(data, "Hook_types", "Hook"),
    }

    rows: list[dict[str, Any]] = []

    def add(component_type: str, component_id: Any, name: Any, tag_type: str, value: Any) -> None:
        if pd.isna(value) or value == "":
            return
        rows.append(
            {
                "component_type": component_type,
                "component_id": component_id,
                "component_name": name,
                "tag_type": tag_type,
                "tag_value": value,
            }
        )

    for _, row in media.iterrows():
        add("media", row.get("id"), row.get("Name"), "Media_Style", dereference(row.get("Media_Style"), lookups["Media_Style"]))
        add("media", row.get("id"), row.get("Name"), "Media_Energy", dereference(row.get("Media_Energy"), lookups["Media_Energy"]))
        add("media", row.get("id"), row.get("Name"), "Gendered", row.get("Gendered"))

    for _, row in headlines.iterrows():
        add("headline", row.get("id"), row.get("Text"), "Tone", dereference(row.get("Tone"), lookups["Tone"]))
        add("headline", row.get("id"), row.get("Text"), "Promise", dereference(row.get("Promise"), lookups["Promise"]))
        add("headline", row.get("id"), row.get("Text"), "Hook", dereference(row.get("Hooks"), lookups["Hook"]))

    for _, row in texts.iterrows():
        add("text", row.get("id"), row.get("Name"), "Hook", dereference(row.get("Hook"), lookups["Hook"]))
        add("text", row.get("id"), row.get("Name"), "Promise", dereference(row.get("Promise"), lookups["Promise"]))
        add("text", row.get("id"), row.get("Name"), "Structure", row.get("Structure"))
        add("text", row.get("id"), row.get("Name"), "Gendered_Grammar", row.get("Gendered_Grammar"))
        add("text", row.get("id"), row.get("Name"), "Target", row.get("Gendered_Target"))

    return pd.DataFrame(
        rows,
        columns=["component_type", "component_id", "component_name", "tag_type", "tag_value"],
    )


def write_csvs(data: dict[str, Any], output_dir: Path) -> dict[str, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    weekly = build_weekly_run_history(data)
    components = build_ad_components(data)
    conversions = build_ad_lifetime_conversions(data)

    tables = {
        "weekly_run_history": weekly,
        "ad_lifetime_summary": build_ad_lifetime_summary(weekly),
        "ad_last_run_summary": build_ad_last_run_summary(weekly),
        "ad_lifetime_conversions": conversions,
        "ad_components": components,
        "component_media_lifetime": build_component_lifetime(
            weekly,
            components,
            id_col="media_id",
            name_col="media_name",
            extra_cols=("media_variant", "media_format"),
        ),
        "component_headline_lifetime": build_component_lifetime(
            weekly,
            components,
            id_col="headline_id",
            name_col="headline_text",
        ),
        "component_text_lifetime": build_component_lifetime(
            weekly,
            components,
            id_col="text_id",
            name_col="text_name",
            extra_cols=("text_variant", "primary_text"),
        ),
        "component_tags": build_component_tags(data),
    }

    row_counts = {}
    for name, df in tables.items():
        path = output_dir / f"{name}.csv"
        df.to_csv(path, index=False)
        row_counts[f"data/structured/{name}.csv"] = len(df)

    return row_counts


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compression_for(path: Path) -> int:
    if path.suffix.lower() in {".zip", ".tar", ".gz", ".tgz", ".mp4", ".mov"}:
        return zipfile.ZIP_STORED
    return zipfile.ZIP_DEFLATED


def build_manifest(files: list[ArtifactFile], repo_root: Path, row_counts: dict[str, int]) -> dict[str, Any]:
    manifest_files = []
    for item in files:
        source = item.source
        try:
            display_source = source.relative_to(repo_root).as_posix()
        except ValueError:
            if item.arcname == "data/performance_data.json":
                display_source = "generated from live Grist via --refresh-grist"
            elif item.arcname.startswith("data/structured/"):
                display_source = "generated from data/performance_data.json"
            else:
                display_source = str(source)
        manifest_files.append(
            {
                "source": display_source,
                "archive_path": item.arcname,
                "size_bytes": source.stat().st_size,
                "sha256": sha256_file(source),
                **({"rows": row_counts[item.arcname]} if item.arcname in row_counts else {}),
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "purpose": "Decision-log evaluation artifact for Facebook ad planning.",
        "notes": [
            "Structured evaluation tables are generated from raw Grist tables in performance_data.json where possible.",
            "ad_lifetime_conversions.csv is generated from Derived_Lifetime_Ad_Conversions because downstream lead outcomes are maintained there.",
        ],
        "files": manifest_files,
    }


def write_zip(files: list[ArtifactFile], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, mode="w") as archive:
        for item in files:
            archive.write(item.source, item.arcname, compress_type=compression_for(item.source))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a standalone decision-log evaluation artifact."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--outputs-dir", default="outputs", help="Directory containing exported data.")
    parser.add_argument("--config", default="config.json", help="Path to config.json.")
    parser.add_argument(
        "--refresh-grist",
        action="store_true",
        help=(
            "Fetch a fresh Grist snapshot into a temp file for this artifact only. "
            "Does not update outputs/performance_data.json."
        ),
    )
    parser.add_argument(
        "--output-zip",
        default="outputs/decision_log_evaluation.zip",
        help="Destination zip path.",
    )
    parser.add_argument(
        "--no-assets",
        action="store_true",
        help="Omit attachments_manifest.json and attachments.tar from the artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    outputs_dir = (repo_root / args.outputs_dir).resolve()
    output_zip = (repo_root / args.output_zip).resolve()
    performance_json = outputs_dir / "performance_data.json"

    if not args.refresh_grist and not performance_json.is_file():
        print(f"Missing required file: {performance_json}")
        print("Run pixi run export_ads_no_attachments or pixi run export_ads first.")
        return 1

    with tempfile.TemporaryDirectory(prefix="decision-log-eval-") as tmp:
        tmp_path = Path(tmp)
        if args.refresh_grist:
            cfg = load_config(args.config)
            ad_cfg = cfg["ad_tracking"]
            client = GristClient(
                ad_cfg["doc_id"],
                ad_cfg["api_key"],
                ad_cfg.get("server", "https://docs.getgrist.com"),
            )
            data = fetch_full_database_dump(
                client,
                download_attachments=False,
                attachments_dir=str(tmp_path / "attachments"),
            )
            performance_json = tmp_path / "performance_data.json"
            performance_json.write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        else:
            data = load_performance_data(str(performance_json))

        structured_dir = tmp_path / "data" / "structured"
        row_counts = write_csvs(data, structured_dir)

        files = [
            ArtifactFile(performance_json, "data/performance_data.json"),
            *[
                ArtifactFile(path, f"data/structured/{path.name}")
                for path in sorted(structured_dir.glob("*.csv"))
            ],
            *[
                ArtifactFile(repo_root / path, f"context/{path}")
                for path in CONTEXT_FILES
                if (repo_root / path).is_file()
            ],
        ]

        if not args.no_assets:
            asset_files = (
                ArtifactFile(outputs_dir / "attachments_manifest.json", "assets/attachments_manifest.json"),
                ArtifactFile(outputs_dir / "attachments.tar", "assets/attachments.tar"),
            )
            missing_assets = [item.source for item in asset_files if not item.source.is_file()]
            if missing_assets:
                print("Missing asset files. Re-run with --no-assets or run pixi run export_ads.")
                for path in missing_assets:
                    print(f"  - {path}")
                return 1
            files.extend(asset_files)

        manifest_path = tmp_path / "decision_log_evaluation_manifest.json"
        manifest = build_manifest(files, repo_root, row_counts)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        files.append(ArtifactFile(manifest_path, "manifest/decision_log_evaluation_manifest.json"))

        write_zip(files, output_zip)

    print(f"Created {output_zip}")
    print("Included structured evaluation tables:")
    for archive_path, rows in sorted(row_counts.items()):
        print(f"  - {archive_path}: {rows} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

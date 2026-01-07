import argparse
import json
import sys
from typing import Any, Dict, List, Optional, Tuple

from grist.grist import GristClient


def _num(x: Any) -> int:
    if x is None:
        return 0
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, (int, float)):
        return int(x)
    s = str(x).strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def build_rollup_by_ad(
    rollup_records: List[Dict[str, Any]], cols: Dict[str, str]
) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for rec in rollup_records:
        fields = rec.get("fields", {})
        ad = (fields.get(cols["ad_name"]) or "").strip()
        if not ad:
            continue  # skip blank/unattributed group
        out[ad] = {
            "total_leads": _num(fields.get(cols["total_leads"])),
            "trial_lessons": _num(fields.get(cols["trial_lessons"])),
            "registered": _num(fields.get(cols["registered"])),
            "failed": _num(fields.get(cols["failed"])),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Copy ad rollups from Leads summary table into Ad tracking Ads table."
    )
    ap.add_argument("--config", required=True, help="Path to config.json")
    ap.add_argument(
        "--dry-run", action="store_true", help="Print changes but do not patch Grist."
    )
    args = ap.parse_args()

    from utils import load_config

    cfg = load_config(args.config)

    leads_cfg = cfg["leads"]
    rollup_cfg = leads_cfg["rollup"]
    ad_cfg = cfg["ad_tracking"]

    leads_client = GristClient(
        leads_cfg["doc_id"],
        leads_cfg["api_key"],
        leads_cfg.get("server", "https://docs.getgrist.com"),
    )
    ad_client = GristClient(
        ad_cfg["doc_id"],
        ad_cfg["api_key"],
        ad_cfg.get("server", "https://docs.getgrist.com"),
    )

    rollup_table_id = rollup_cfg["table_id"]
    rollup_cols = rollup_cfg["columns"]

    ads_table_id = ad_cfg["ads_table_id"]
    ad_cols = ad_cfg["columns"]

    rollup_records = leads_client.fetch_records(rollup_table_id)
    rollup_by_ad = build_rollup_by_ad(rollup_records, rollup_cols)

    if not rollup_by_ad:
        print(
            "[WARN] No rollup rows found (or all were blank Ad name). Nothing to update."
        )
        return

    ads_records = ad_client.fetch_records(ads_table_id)

    # Map existing Ads rows by ad name
    ads_by_name: Dict[str, Tuple[int, Dict[str, Any]]] = {}
    for rec in ads_records:
        rec_id = rec.get("id")
        fields = rec.get("fields", {})
        name = (fields.get(ad_cols["ad_name"]) or "").strip()
        if rec_id is not None and name:
            ads_by_name[name] = (rec_id, fields)

    updates: List[Dict[str, Any]] = []
    missing_in_ads: List[str] = []

    for ad_name, metrics in rollup_by_ad.items():
        if ad_name not in ads_by_name:
            missing_in_ads.append(ad_name)
            continue

        rec_id, current_fields = ads_by_name[ad_name]
        new_fields = {
            ad_cols["total_leads"]: metrics["total_leads"],
            ad_cols["trial_lessons"]: metrics["trial_lessons"],
            ad_cols["registered"]: metrics["registered"],
            ad_cols["failed"]: metrics["failed"],
        }

        # Only patch if something changes
        changed = False
        for k, v in new_fields.items():
            if _num(current_fields.get(k)) != _num(v):
                changed = True
                break

        if changed:
            updates.append({"id": rec_id, "fields": new_fields})

    if missing_in_ads:
        print(
            "[WARN] These Ad names exist in the rollup but not in Ad tracking-Ads (skipping):"
        )
        for n in sorted(missing_in_ads):
            print(f"  - {n}")

    print(f"[INFO] Rollup rows: {len(rollup_by_ad)}")
    print(f"[INFO] Ads rows: {len(ads_by_name)}")
    print(f"[INFO] Rows to update: {len(updates)}")

    if args.dry_run:
        for u in updates[:25]:
            print(f"[DRY-RUN] Would patch record id={u['id']} fields={u['fields']}")
        if len(updates) > 25:
            print(f"[DRY-RUN] ... plus {len(updates) - 25} more.")
        return

    # Patch in chunks
    CHUNK = 200
    for i in range(0, len(updates), CHUNK):
        ad_client.patch_records(ads_table_id, updates[i : i + CHUNK])

    print("[DONE] Updated Ad tracking-Ads from Leads rollup.")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as e:
        print(f"[ERROR] HTTP error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

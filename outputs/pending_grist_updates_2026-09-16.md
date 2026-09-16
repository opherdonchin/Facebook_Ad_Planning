# Pending Grist refresh after the 2026-09-16 API quota limit

> **INVALIDATED:** Do not apply the pending lead or CPL values below. The Meta
> sync double-counted lead aliases. See `weekly_source_validation.md`; a W23+
> audited backfill and complete downstream regeneration are required first.

The Meta W37 sync completed successfully at approximately 12:17 IDT. Immediately afterward, Grist returned `429 Exceeded monthly API limit for this site` (`3,001 / 3,000` calls), so the remaining Grist-derived tables could not be refreshed through the API.

## Values to write when access resumes

- `Weekly_Summary`, `2026-W37`: `Total_spent = 380.00`, `Num_leads = 12`, calculated CPL `31.6667`.
- These are all-delivery totals and include the non-intended `Mens Ad B` residue of ₪7.23. The intended portfolio is ₪372.77 / 12 leads / ₪31.06.

## Commands to replay

```bash
pixi run python src/run_transforms.py lifetime_ad_conversions_prod --input-profile leads --output-profile ad_tracking
pixi run transform_weekly
pixi run python src/run_transforms.py component_media_lifetime_metrics_prod component_headline_lifetime_metrics_prod component_text_lifetime_metrics_prod --profile ad_tracking
pixi run export_ads
pixi run package_uploads
```

Until then, the locally packaged weekly bundles are current for the captured Meta snapshot. They were rebuilt from `outputs/w37_meta_snapshot_2026-09-16.json` by `src/refresh_export_from_meta_snapshot.py`. `performance_data.json` contains an `offline_refresh` disclosure. The local `Derived_Lifetime_Ad_Conversions` table remains stale and must not be used; the reconciled `Ads` rollups and the membership reconciliation report contain the corrected lead/trial/registration/failure counts.

# Weekly source validation — 2026-W37

**Status: FAILED — do not use the current W37 exports for planning or posting.**

## Reporting window

- Meta account dates: 2026-09-10 through 2026-09-16, inclusive
- Meta account timezone: `America/Los_Angeles`
- Original snapshot: approximately 2026-09-16 12:17 IDT / 02:17 PDT
- Week status at capture: open and provisional

## Reconciliation result

The original sync added two Meta action aliases for the same Instant Form
submissions. Correct source counts select `onsite_conversion.lead_grouped` and
use `lead` only as a fallback.

Evidence came from read-only Meta Marketing API v25.0 daily-insights queries and
the Instant Form lead endpoint. The original raw response was not frozen as a
checksummed artifact before the faulty write, and no independent Ads Manager
export was preserved. That is sufficient to invalidate the current data, but
not sufficient to mark a repaired backfill as passed.

| Ad | Snapshot spend | Stored leads | Source leads | Result |
|---|---:|---:|---:|---|
| M 2609_1 | ₪74.04 | 0 | 0 | Count matches |
| Mens Ad B | ₪7.23 | 0 | 0 | Count matches; residual delivery |
| Mens Ad J | ₪118.73 | 4 | 2 | **Failed: doubled** |
| W 2603_1 | ₪0.27 | 0 | 0 | Count matches |
| Womens Ad G | ₪179.73 | 8 | 4 | **Failed: doubled** |

The later `Mens Ad J` spend of approximately ₪122.18 is explained by additional
September 16 delivery after the 12:17 IDT snapshot. It does not explain the lead
difference.

Correct frozen-snapshot totals are:

- Intended delivery: ₪372.77 / 6 leads / ₪62.13 CPL
- All delivery: ₪380.00 / 6 leads / ₪63.33 CPL
- Mens Ad J: ₪118.73 / 2 / ₪59.37 CPL
- Womens Ad G: ₪179.73 / 4 / ₪44.93 CPL

## Scope and consequences

- The same alias double-counting is verified in API-synced data from W23
  onward.
- W23 also contains duplicate partial-week and Wednesday-end rows and cannot be
  repaired by merely halving lead counts.
- Weekly, current-run, lifetime, component, tag, and candidate-ranking exports
  derived from the affected rows are not validated.
- The provisional W38 recommendation is invalid. Under the corrected W37
  snapshot, Mens Ad J changes from keep rule 1 to replace rule 3; Womens Ad G
  remains a keep.
- Do not replay the values in `pending_grist_updates_2026-09-16.md`.
- The old `weekly_upload_*.zip` files and manifest were moved to
  `outputs/invalidated_w37_2026-09-16/` so they cannot be mistaken for current
  upload bundles.

## Repair status

- Future aggregation logic has a regression test and now treats the Meta action
  names as ordered fallbacks rather than additive events.
- Test suite after the current safety changes: `pixi run pytest` on 2026-09-16,
  86 passed (8 deprecation warnings).
- Historical Grist rows have **not** yet been repaired.
- Downstream exports and the W37 review have **not** yet been regenerated.

Validation remains failed until W23 onward is audited/backfilled from Meta,
Grist is read back, all derived artifacts are regenerated, and this file is
replaced with a passing post-close validation record.

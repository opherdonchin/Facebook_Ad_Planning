# Weekly source validation — 2026-W39 authoritative early decision report

**Status: PASSED — AUTHORITATIVE DECISION REPORT — EARLY**

This Wednesday report is authoritative for the Thursday decision cycle under
the repository reporting policy. It is not provisional. The final Meta account
day was open at capture time, so the exact capture times and the small accrued
spend difference between the two primary-source API views are recorded below.

## Reporting window

- Meta account dates: 2026-09-24 through 2026-09-30, inclusive
- Assessed data week: 2026-W39
- Decision week: 2026-W40
- Meta account timezone: `America/Los_Angeles`
- Frozen daily snapshot capture: 2026-09-30 07:15:38 UTC / 10:15:38 IDT / 00:15:38 PDT
- Snapshot: `outputs/meta_source_2026-09-24_2026-09-30_early_20260930T1015IDT.json`
- Snapshot SHA-256: `a419b87d7079268dda154a50549503aba97085395990f62042b0f3425939980d`
- Independent weekly-grain query: started 2026-09-30 07:16:09 UTC / 00:16:09 PDT;
  finished 07:16:12 UTC / 00:16:12 PDT
- Final account day status: **open** at both captures; Wednesday had only just
  begun in the Meta account timezone.
- Results metric: Instant Form submissions, using ordered aliases
  `onsite_conversion.lead_grouped` then `lead`; aliases were never added.
- Attribution setting: `1d_view_7d_click` from the configured Meta account
  source workflow.

## Frozen per-ad source values

Values below were produced by the documented `pixi run fetch_weekly_runs`
dry-run from daily ad-level Meta Insights rows.

| Ad | Meta ad ID | Spend | Results | Intended run |
|---|---:|---:|---:|---|
| M 2609_2 | 52682362107668 | ₪51.64 | 0 | Yes |
| Mens Ad J | 6997707368064 | ₪384.45 | 2 | Yes |
| W 2603_1 | 52540302039868 | ₪32.04 | 1 | Yes |
| Womens Ad G | 6963149336864 | ₪334.28 | 1 | Yes |

Authoritative early portfolio total: ₪802.41 spend / 4 Results / ₪200.60 CPL.

## Independent primary-source reconciliation

The comparison was a one-off read-only Facebook Graph API Insights query at
`level=ad`, `time_increment=all_days`, for the same exact date range. It was
queried separately from the daily snapshot client and aggregation path.

| Ad | Daily snapshot spend | Weekly-grain API spend | Spend delta | Daily Results | Weekly Results | Lead/alias check |
|---|---:|---:|---:|---:|---:|---|
| M 2609_2 | ₪51.64 | ₪51.88 | +₪0.24 | 0 | 0 | Pass |
| Mens Ad J | ₪384.45 | ₪384.45 | ₪0.00 | 2 | 2 | Pass |
| W 2603_1 | ₪32.04 | ₪32.04 | ₪0.00 | 1 | 1 | Pass |
| Womens Ad G | ₪334.28 | ₪334.28 | ₪0.00 | 1 | 1 | Pass |

- All four Results counts matched exactly.
- No lead-action alias disagreement occurred in either view.
- The ₪0.24 M 2609_2 spend difference is open-day accrual between captures;
  the two views were captured 31 seconds apart while the final account day was
  open. It is not a closed-week discrepancy.
- No ad was missing, skipped, or unmatched.

## Tests, write, and read-back

- `pixi run pytest`: **86 passed**, 8 dependency deprecation warnings.
- Team-site read-only preflight: `ad_tracking` 21 tables / 48 Creative records;
  `leads` 11 tables / 486 Leads records; linked Students document 6 tables /
  133 Student records.
- Snapshot replay: 0 inserts, 4 updates, 0 skipped ads.
- Grist read-back from team `ad_tracking.Weekly_runs`: rows 279–282 matched
  week `2026-09-30`, ad identity, spend, Results, and `Intended_run=True`.
- Meta Leads sync: 4 forms checked, 7 leads fetched, 0 created, 0 updated,
  0 errors; 7 known duplicate-key warnings were retained without changes.
- Ads rollup update: 1 Ads row updated from the team Leads document.

## Downstream regeneration

Completed on 2026-09-30 from the Isshin Aikido team documents:

- `pixi run transform_weekly`: weekly 272 rows, lifetime 52 rows, last-run 51
  rows, tag rollups 46 rows, component tags 224 rows.
- `pixi run export_ads`: refreshed `performance_data.json`, eight structured
  CSVs, 82 attachments, `attachments_manifest.json`, and `attachments.tar`.
- Export completed before 2026-09-30 10:19 IDT; packaging follows this note.

This is an authoritative early decision report for the Thursday update. A
post-close refresh may change open-day spend or late-attributed Results, but it
does not retroactively make this captured report provisional. If those changes
materially alter a decision, record a correction or re-evaluation separately.

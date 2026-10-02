# Plan for 2026-W40 (assessing 2026-W39)

**Status: AUTHORITATIVE DECISION REPORT — EARLY**  
**Decision captured:** 2026-09-30, Wednesday, 10:15 IDT  
**Source week:** 2026-09-24 through 2026-09-30, inclusive

This is the authoritative early report for the Thursday update. It is not
provisional. The final Meta account day was still open at capture time. Any
post-close change is a correction or re-evaluation against this report, not a
reason to relabel this report as provisional.

## Source and integrity record

- **Source documents:** Isshin Aikido team Grist documents, not the personal
  Grist account. `ad_tracking` is on `https://isshinaikido.getgrist.com`; the
  read-only preflight found 21 tables and 48 Creative records. `leads` is on
  the same team site; the preflight found 11 tables and 486 Leads records.
- **Meta account timezone:** `America/Los_Angeles`.
- **Results metric:** Instant Form submissions. The source workflow gives
  priority to `onsite_conversion.lead_grouped`, then `lead`; aliases were never
  added together.
- **Daily snapshot:**
  `outputs/meta_source_2026-09-24_2026-09-30_early_20260930T1015IDT.json`
- **Snapshot capture:** 2026-09-30 07:15:38 UTC / 10:15:38 IDT / 00:15:38
  PDT.
- **Snapshot SHA-256:**
  `a419b87d7079268dda154a50549503aba97085395990f62042b0f3425939980d`
- **Independent reconciliation:** a separate read-only Facebook Graph API
  Insights query at `level=ad`, `time_increment=all_days`, using the same
  dates. It started at 07:16:09 UTC and finished at 07:16:12 UTC, 31 seconds
  after the daily snapshot.

The daily snapshot and weekly-grain Facebook API query matched on all four
lead counts and on three of four spend values. `M 2609_2` differed by ₪0.24
(₪51.64 versus ₪51.88), which is open-day accrual between two captures. There
was no unexplained lead difference and no closed-week spend discrepancy.

## Validated W39 performance

| Campaign | Ad | Spend | Leads | CPL | Rule | Decision |
|---|---|---:|---:|---:|---|---|
| M | Mens Ad J | ₪384.45 | 2 | ₪192.23 | Replace: spend >20, CPL ≥50, run ≥60 | Replace |
| M | M 2609_2 | ₪51.64 | 0 | — | Replace: spend >20, zero leads, run ≥60 | Replace |
| W | Womens Ad G | ₪334.28 | 1 | ₪334.28 | Replace: spend >20, CPL ≥50, run ≥60 | Replace |
| W | W 2603_1 | ₪32.04 | 1 | ₪32.04 | Keep: spend >20, CPL <50 | Keep |

**Portfolio total:** ₪802.41 / 4 leads / ₪200.60 CPL.

Run evidence used for the replacement decisions:

- `Mens Ad J`: W37–W39, ₪651.67 / 5 leads / ₪130.33 CPL.
- `M 2609_2`: W38–W39, ₪114.73 / 0 leads.
- `Womens Ad G`: W35–W39, ₪893.31 / 10 leads / ₪89.33 CPL.
- `W 2603_1`: W37–W39, ₪119.90 / 1 lead / ₪119.90 CPL.

## Replacement-slot logic

The assessed and immediately prior completed weeks are W39 and W38.

- **Men:** W38 included the complete-new launch `M 2609_2`; there was no
  complete-new launch in W39. Two male replacement slots are required. The
  decision table therefore calls for one complete-new ad plus one reuse when
  fewer than two strong reuse candidates exist. No male candidate is strong
  under the current thresholds, so the highest-ranked weak reuse fills one
  slot and a complete-new fills the other.
- **Women:** There was no complete-new launch in W38 or W39. One female
  replacement slot is required, so it must be a complete-new ad.

## Ordered reuse candidates

Active ads were excluded from their own gender's candidate list. Candidates
are ordered by the documented reuse ranking. “Prior run CPL” is the assessed
historical run measure; lifetime CPL is shown as a secondary reference.

### Men

No strong male reuse candidates.

| Rank | Candidate | Prior run CPL | Lifetime CPL | Last seen | Lifetime leads |
|---:|---|---:|---:|---|---:|
| 1 | M 2603_1 | ₪63.37 | ₪64.32 | W12 | 4 |
| 2 | M 2602_1 | ₪71.33 | ₪71.33 | W10 | 4 |
| 3 | Mens Ad C | ₪73.12 | ₪73.12 | 2025-W40 | 5 |
| 4 | M 2603_3 | ₪74.15 | ₪74.15 | W14 | 2 |
| 5 | Mens Ad N | ₪74.44 | ₪60.52 | W20 | 8 |
| 6 | Mens Ad M | ₪76.43 | ₪76.43 | 2025-W51 | 4 |
| 7 | Mens Ad H | ₪76.65 | ₪76.65 | 2025-W43 | 3 |
| 8 | M 2609_1 | ₪81.71 | ₪83.21 | W37 | 2 |
| 9 | M 2607_1 | ₪87.02 | ₪87.02 | W33 | 6 |
| 10 | Mens Ad B | ₪91.31 | ₪54.79 | W36 | 33 |
| 11 | Mens Ad D | ₪95.37 | ₪95.37 | 2025-W36 | 1 |
| 12 | M 2605_1 | ₪97.19 | ₪97.19 | W24 | 2 |
| 13 | Mens Ad E | ₪103.58 | ₪108.23 | 2025-W40 | 2 |
| 14 | Mens Ad F | ₪105.20 | ₪125.13 | 2025-W41 | 1 |
| 15 | Mens Ad O | ₪113.09 | ₪126.56 | W07 | 1 |
| 16 | M 2604_1 | ₪200.84 | ₪232.02 | W18 | 1 |
| 17 | Mens Ad A | — | ₪50.13 | W33 | 26 |

### Women

Strong candidates, in order:

1. `Womens Ad O` — prior run CPL ₪58.50, lifetime CPL ₪58.50, last seen
   W03, 2 lifetime leads.
2. `Womens Ad A` — prior run CPL ₪111.37, lifetime CPL ₪47.51, last seen
   W35, 39 lifetime leads.

Weak candidates, in order:

1. `W 2603_4` — prior run CPL ₪60.32, lifetime CPL ₪60.32, last seen W16,
   5 leads.
2. `W 2605_1` — ₪61.63 / ₪61.63, last seen W23, 4 leads.
3. `Womens Ad N` — ₪61.81 / ₪61.81, last seen W03, 3 leads.
4. `Womens Ad Q` — ₪62.04 / ₪71.32, last seen W04, 2 leads.
5. `Womens Ad B` — ₪68.90 / ₪65.21, last seen 2025-W33, 5 leads.
6. `W 2602_3` — ₪70.05 / ₪70.05, last seen W07, 2 leads.
7. `Womens Ad M` — ₪71.76 / ₪71.76, last seen 2025-W51, 4 leads.
8. `Womens Ad F` — ₪74.85 / ₪74.85, last seen W35, 1 lead.
9. `Womens Ad E` — ₪80.59 / ₪80.59, last seen W34, 1 lead.
10. `Womens Ad I` — ₪82.71 / ₪82.71, last seen 2025-W40, 3 leads.
11. `Womens Ad D` — ₪118.67 / ₪59.13, last seen W18, 16 leads.
12. `W 2606_1` — ₪124.56 / ₪127.46, last seen W30, 8 leads.
13. `Womens Ad L` — ₪147.46 / ₪147.46, last seen 2025-W49, 1 lead.
14. `W 2603_2` — ₪159.88 / ₪83.95, last seen W22, 5 leads.
15. `W 2607_1` — ₪270.34 / ₪270.34, last seen W33, 2 leads.
16. `Womens Ad P` — ₪295.17 / ₪70.24, last seen W25, 17 leads.
17. `Womens Ad R` — prior run CPL — / lifetime CPL ₪96.91, last seen W05,
    1 lead.
18. `W 2026-W06 2` — prior run CPL — / lifetime CPL ₪111.12, last seen W09,
    1 lead.
19. `W 2602_4` — prior run CPL — / lifetime CPL ₪95.20, last seen W17,
    2 leads.
20. `Womens Ad J` — prior run CPL — / lifetime CPL ₪83.38, last seen W20,
    6 leads.

`M 2603_2` was excluded from the women list because its campaign/name
identity is inconsistent with the women candidate set; it remains a cleanup
item rather than a recommendation.

## Decision for W40

| Campaign | Slot | Recommendation | Basis |
|---|---:|---|---|
| M | 1 | Reuse `M 2603_1` | Highest-ranked available male reuse; no strong male reuse exists |
| M | 2 | Complete-new `M 2609_3` | Required by the two-slot rule after one reuse slot |
| W | 1 | Complete-new `W 2609_2` | No complete-new women’s launch in W38 or W39 |
| W | retained | Keep `W 2603_1` | W39 CPL ₪32.04, below the keep threshold |

### Complete-new male ad: M 2609_3

- **Media:** `outputs/creative_generation/M_2609_3_beginner_balance_photo.png`
  — two adult male beginners practicing an upright forearm-guidance balance
  exercise; `Photo - Dojo / Instructional`.
- **Headline:** `יציבות לומדים בתנועה`
- **Primary text concept:** `Steady Movement`; hook `Stability / Balance`;
  promise `Body Capability`; tone `Direct`; structure `Checklist`;
  masculine.
- **Primary text:**

  > לא צריך להגיע מוכן. יציבות היא משהו שלומדים דרך תנועה ותרגול.
  >
  > • לומדים לשמור על שיווי משקל גם כשהכיוון משתנה
  > • מתרגלים תנועה מדויקת עם שותף ובקצב הדרגתי
  > • בונים ביטחון בגוף בלי כוחנות ובלי תחרות
  >
  > האימונים למבוגרים בלב באר שבע.
  >
  > השאר פרטים לשיעור היכרות ללא התחייבות.

- **Same-gender reshuffle fallback:** media
  `Outside_Sunset_MM_Kaitenage_photo__B.png`, headline `כוח רגוע מבפנים`,
  text `Everyday Pressure`. This fallback is a component reshuffle only and
  is not the primary recommendation.

### Complete-new female ad: W 2609_2

- **Media:** `outputs/creative_generation/W_2609_2_guided_turn_photo.png`
  — two adult female beginners learning a controlled stepping turn;
  `Photo - Dojo / Instructional`.
- **Headline:** `לגלות מה הגוף שלך יכול`
- **Primary text concept:** `Discover Capability`; hook `Meaning / Growth`;
  promise `Body Capability`; tone `Affirmative`; structure `Checklist`;
  feminine.
- **Primary text:**

  > לא צריך ניסיון קודם כדי לגלות תנועה חדשה ויכולת שלא הכרת.
  >
  > • לומדות לנוע ביציבות גם כשהכיוון משתנה
  > • מתרגלות תיאום ודיוק עם שותפה ובקצב הדרגתי
  > • מגלות ביטחון חדש בגוף בלי תחרות ובלי לחץ
  >
  > האימונים למבוגרות בלב באר שבע.
  >
  > השאירי פרטים לשיעור היכרות ללא התחייבות.

- **Same-gender reshuffle fallback:** media
  `Dojo_Instruction_FemalePair.png`, headline `תנועה. עוצמה. חיוך.`, text
  `Meaningful Movement`. This fallback is a component reshuffle only and is
  not the primary recommendation.

## Operational completion

- The validated snapshot was replayed to team `ad_tracking.Weekly_runs`; four
  rows were updated and read back exactly.
- `pixi run sync_meta_leads`: 4 forms checked, 7 leads fetched, 0 created,
  0 updated, 0 errors.
- `pixi run update_ads`: one Ads row updated from the team Leads rollup.
- `pixi run transform_weekly` and `pixi run export_ads` completed from the
  Isshin Aikido team documents.
- `pixi run package_uploads` completed; the three upload bundles passed local
  member, readability, and CRC verification.

No Meta ad changes were made by this report. The recommendations above are
the W40 decision package for implementation and later post-close evaluation.

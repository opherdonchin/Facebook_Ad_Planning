> **INVALIDATED 2026-09-16:** Do not use this draft for posting or ad changes.
> The Meta sync doubled nonzero lead counts by adding two action aliases for the
> same submissions. Historical W23+ rows and all downstream metrics require
> repair and regeneration. See `weekly_source_validation.md`.

## Readiness confirmation

Status: **ready for a complete provisional evaluation; not approval-ready for a final W38 switch or decision-log commit.**

All three bundles generated at **2026-09-16 12:31:49 IDT** opened successfully. Every embedded file matched its manifest size and SHA-256; the three manifest copies were identical.

- `weekly_upload_data.zip`: all nine data files and manifest read.
- `weekly_upload_assets.zip`: attachment manifest, TAR, and manifest read. All 80 declared assets were present.
- `weekly_upload_context.zip`: decision log, schema, format, metrics, project guide, taxonomy, heuristics, weekly prompt, and manifest read.
- Missing, unreadable, or unprocessed files: **none**.
- The four proposed W38 ads’ source media and finished creative thumbnails were visually inspected.
- The corrected reconciliation, advertising assessment, and pending-Grist-update report were also reviewed.

Known freshness limitation:

- The Meta snapshot was captured around **12:17 IDT**, while W37 was still open.
- Grist reached its 3,000-call monthly API limit after the W37 rows were written. The packaged export was refreshed locally from that exact snapshot, including recalculated W37 CPL and `Performing` fields.
- `Derived_Lifetime_Ad_Conversions` remains stale and was not used.
- `Weekly_Summary` could not be updated; its pending W37 all-delivery values are ₪380.00, 12 leads, and ₪31.67 CPL.
- The corrected `Ads` rollups and reconciliation report were used for post-lead context.
- The reconciliation’s 130/130 verification proves Student→Lead reciprocity; I did not treat it as a separate inverse Registration-Lead→Student assertion.

## Week disambiguation

- **Latest completed data week:** 2026-W36.
- **Open snapshot evaluated provisionally:** 2026-W37, Thursday September 10 through Wednesday September 16.
- **Decision/planned week:** 2026-W38, provisionally.
- **Current intended runs through the snapshot:**
  - `Mens Ad J`: W37 only.
  - `M 2609_1`: W36–W37.
  - `Womens Ad G`: W35–W37.
  - `W 2603_1`: W37 only.
- `Mens Ad B` had ₪7.23 of non-intended residual W37 delivery. It does not extend its W34–W36 intended run.
- The decision log currently ends with the W36 plan. W37 intent is nevertheless unambiguous from the explicit `Intended_run` flags.

# 1. Performance summary

### Campaign-level snapshot

| Scope | W36 spend | W36 leads | W36 CPL | W37 intended spend | W37 leads | W37 CPL | Change |
|---|---:|---:|---:|---:|---:|---:|---|
| Men | ₪210.59 | 4 | ₪52.65 | ₪192.77 | 4 | ₪48.19 | Spend −₪17.82; leads flat; CPL −₪4.46 |
| Women | ₪199.24 | 6 | ₪33.21 | ₪180.00 | 8 | ₪22.50 | Spend −₪19.24; leads +2; CPL −₪10.71 |
| Intended portfolio | ₪409.83 | 10 | ₪40.98 | ₪372.77 | 12 | ₪31.06 | Spend −9.0%; leads +20%; CPL −24.2% |
| All W37 delivery | — | — | — | ₪380.00 | 12 | ₪31.67 | Includes ₪7.23 Mens Ad B residue |

### Ad-level performance and deltas

| Ad | Intent | W37 spend | Leads | CPL | Change from W36 | Flag |
|---|---|---:|---:|---:|---|---|
| Mens Ad J | Intended | ₪118.73 | 4 | ₪29.68 | Reintroduced: +₪118.73, +4 leads | No low-sample flag |
| M 2609_1 | Intended | ₪74.04 | 0 | — | Spend −₪15.33; leads 4→0; CPL ₪22.34→— | Weekly low sample; meaningful zero-lead spend |
| Womens Ad G | Intended | ₪179.73 | 8 | ₪22.47 | Spend +₪55.22; leads +2; CPL +₪1.71 | No low-sample flag |
| W 2603_1 | Intended | ₪0.27 | 0 | — | Reintroduced with negligible delivery | Low sample and clear non-delivery |
| Mens Ad B | Non-intended residue | ₪7.23 | 0 | — | Spend −₪113.99 | Excluded from decisions |

### Current-run and lifetime evidence

| Ad | Current intended run | Run spend / leads / CPL | Lifetime spend / leads / CPL |
|---|---|---|---|
| Mens Ad J | W37 | ₪118.73 / 4 / ₪29.68 | ₪3,949.71 / 101 / ₪39.11 |
| M 2609_1 | W36–W37 | ₪163.41 / 4 / ₪40.85 | ₪166.40 / 4 / ₪41.60 |
| Womens Ad G | W35–W37 | ₪396.98 / 16 / ₪24.81 | ₪785.88 / 22 / ₪35.72 |
| W 2603_1 | W37 | ₪0.27 / 0 / — | ₪609.21 / 17 / ₪35.84 |
| Mens Ad B | Prior run W34–W36 | ₪365.18 / 8 / ₪45.65 | ₪1,808.08 / 38 / ₪47.58 |

### Important observations

- **Actionable observation:** `M 2609_1` reversed from four W36 leads at ₪22.34 CPL to zero W37 leads after ₪74.04. Its two-week run remains acceptable overall, but keep rule 5 still requires replacement once a zero-lead week and current-run spend above ₪60 coincide.
- **Learning signal:** `Womens Ad G` scaled from six to eight leads while CPL remained near ₪22. Its W35–W37 run is the strongest current portfolio result.
- **Confirming signal:** `Mens Ad J` returned with four leads at ₪29.68, consistent with its deep lifetime evidence.
- **Actionable delivery observation:** `W 2603_1` received only ₪0.27. This is an operational delivery problem, not evidence of creative failure. The corrected intended-only run logic means its current run is ₪0.27—not the old bridged historical total.
- **Possibly noise:** the portfolio-level W37 improvement is encouraging, but W37 is still open and much of the women’s result comes from one ad.

# 2. Summary of the current situation

### Current understanding by category

| Category | Current read |
|---|---|
| Ads | `Mens Ad J` and `Womens Ad G` are clear keeps. `M 2609_1` triggers replacement mechanically. `W 2603_1` is retained only because its new intended run has almost no spend. `M 2607_1` is the top eligible men’s reuse. |
| Tags | Strong current combinations span distinct ideas: quiet strength/control for men and stress-to-energy/body capability for women. Tag rollups support reflective headlines, strength-without-force hooks, and question-led text, but remain confounded by ad combinations. |
| Headlines | `כוח שקט, שליטה ברגע` has ₪39.11 lifetime CPL. `עוצמה, רוגע, ובטחון עצמי` has ₪48.21 component CPL. `ללמוד לשלוט ברגע` is weaker in aggregate at ₪52.00 but performed at ₪43.51 in `M 2607_1`. |
| Texts | `Screens To Energy` is at ₪35.72 CPL; `Stable Without Struggle` ₪39.79; `Time Out For You — Dad 2607 refresh` ₪43.51; `Quiet Space - Bullet Calm` ₪43.61. |
| Media | `Tenshinage_lineart_controlled` is deeply proven at ₪39.11 over 101 leads. `SumoOtoshi_MF_AiArt` is ₪35.72 over 22. `Outside_Sunset_MM_Kaitenage_photo_v2` is ₪43.51 over 12. `Shihonage_MF_Dojo_Photo` is ₪49.04 across six ads. |
| Combinations | The selected ads are better treated as full combinations than as isolated component effects. Several components appear in only one ad, while others perform differently across combinations. |

### What the agent should remember

- W37 is open; this is not yet a final completed-week decision.
- Use intended delivery for run construction. Residual spend must not bridge runs.
- Do not use the stale lifetime-conversion derived table.
- `M 2609_1` is being replaced because of the explicit weekly rule, not because its lifetime or two-week average is intrinsically poor.
- The prior-week complete-new requirement is satisfied: `M 2609_1` and `W 2609_1` were complete-new launches in W36. Therefore a men’s replacement in W38 should be reuse, not another complete-new ad.
- No new tags are needed.

### What the human should notice

- Lead generation is currently efficient, but student growth depends on post-lead handling. The corrected Ads rollups show:

| Planned ad | Matched CRM leads | Trials | Registrations | Failed |
|---|---:|---:|---:|---:|
| Mens Ad J | 59 | 9 | 4 | 50 |
| M 2607_1 | 6 | 0 | 0 | 5 |
| Womens Ad G | 11 | 0 | 0 | 7 |
| W 2603_1 | 12 | 0 | 0 | 12 |

These totals do not fully reconcile to Meta lifetime leads, so they should not override the documented weekly CPL rules. They do reinforce the need to focus on contact, booking, and trial attendance—especially for women.

- The corrected March–August membership flow is nine registrations and seven cancellations, not twelve cancellations. Recorded cancellations average 1.17 per month.
- The recommended budget for roughly +1 active student per month remains about **₪2,900/month**, allocated approximately 70% men and 30% women. Current spend near ₪1,800–₪1,900 is consistent with little practical growth.
- `Womens Ad G` is a lead-generation winner but does not yet have recorded registrations in the corrected ad rollup. Lead quality should be allowed to mature and then reviewed.
- `W 2603_1` is a keep under the current rule, but a slot that repeatedly receives no delivery is not useful indefinitely.

# 3. Key decisions

## Reuse candidate lists

Eligibility excludes the four W37 intended ads. `Mens Ad B` remains eligible because its W37 activity is explicitly non-intended residue.

### Men

Strong candidates, ranked:

| Rank | Ad | Most recent intended-run CPL | Lifetime CPL | Last intended run |
|---:|---|---:|---:|---|
| 1 | M 2607_1 | ₪43.51 | ₪43.51 | W31–W33 |
| 2 | Mens Ad B | ₪45.65 | ₪47.58 | W34–W36 |
| 3 | M 2605_1 | ₪51.78 | ₪51.78 | W21–W24 |

Weak candidates in required run-CPL order: `M 2603_1`, `M 2602_1`, `Mens Ad C`, `M 2603_3`, `Mens Ad N`, `Mens Ad M`, `Mens Ad H`, `Mens Ad D`, `Mens Ad E`, `Mens Ad F`, `Mens Ad O`, `M 2604_1`, `Mens Ad A` (no calculable latest-run CPL).

### Women

Strong candidates, ranked:

| Rank | Ad | Most recent intended-run CPL | Lifetime CPL | Last intended run |
|---:|---|---:|---:|---|
| 1 | W 2605_1 | ₪51.78 | ₪51.78 | W20–W23 |
| 2 | Womens Ad A | ₪55.68 | ₪44.12 | W34–W35 |
| 3 | Womens Ad O | ₪58.50 | ₪58.50 | W02–W03 |

Weak candidates in required order: `W 2603_4`, `Womens Ad N`, `Womens Ad Q`, `W 2606_1`, `Womens Ad B`, `W 2602_3`, `Womens Ad M`, `Womens Ad F`, `Womens Ad E`, `Womens Ad I`, `Womens Ad D`, `W 2607_1`, `M 2603_2` (canonical campaign is W despite its name), `Womens Ad L`, `Womens Ad P`, `W 2603_2`, then the no-calculable-run-CPL candidates `Womens Ad R`, `W 2026-W06 2`, `W 2602_4`, and `Womens Ad J`.

## Ads to keep

| Campaign | Ad | Rule and evidence | Existing tag combination |
|---|---|---|---|
| Men | Mens Ad J | Rule 1: ₪118.73, 4 leads, ₪29.68 CPL | Line Art + Dynamic/Throw; Strength Without Force → Calm Under Pressure, Reflective; Stability/Balance → Confidence/Self-Trust, Question Hook |
| Women | Womens Ad G | Rule 1: ₪179.73, 8 leads, ₪22.47 CPL | Poster + Instructional; Stress/Mental Load → Confidence/Self-Trust, Poetic; Energy/Screens → Body Capability, Question Hook |
| Women | W 2603_1 | Rule 6: ₪0.27 weekly/current-run spend, below ₪60 | Photo Art + Instructional; Energy/Screens → Energy/Renewal, Playful; Stress/Mental Load → Calm Under Pressure, Checklist |

## Ads to replace

| Campaign | Ad | Rule and evidence |
|---|---|---|
| Men | M 2609_1 | Rule 5: ₪74.04 W37 spend, zero leads, and ₪163.41 current-run spend |
| Women | None | Both intended ads meet keep rules |

## Reuse ads

| Campaign | Selected ad | Prior run | Lifetime | Tags | Justification |
|---|---|---|---|---|---|
| Men | M 2607_1 | ₪522.11 / 12 leads / ₪43.51 CPL | Same | Outside Photo + Meditative/Inspirational; Meaning/Growth → Focus/Clarity, Reflective; Care Load/No Time → Calm Under Pressure, Checklist | Top strong men’s reuse candidate; inactive since W33; complete-new men’s ad already launched in W36 |
| Women | None | — | — | — | No replacement slot |

## Complete new ads

| Campaign | Recommendation |
|---|---|
| Men | None |
| Women | None |

## Reshuffle fallbacks

| Campaign | Recommendation |
|---|---|
| Men | None required because no complete-new ad is proposed |
| Women | None required because no complete-new ad is proposed |

## Creative and provenance verification

| Planned ad | Canonical media and archive path | Visual-semantic result |
|---|---|---|
| Mens Ad J | `Tenshinage_lineart_controlled` — `attachments/Media/Tenshinage_lineart_controlled.jpg` | Controlled male-pair technique supports quiet strength, stability, and control without aggression. |
| M 2607_1 | `Outside_Sunset_MM_Kaitenage_photo_v2`, variant `B 2607 refresh` — `attachments/Media/Outside_Sunset_MM_Kaitenage_photo_v2__B 2607 refresh.png` | Adult paired technique and balance break support “learn to control the moment”; the dad/time-for-yourself copy remains compatible with the male target. |
| Womens Ad G | `SumoOtoshi_MF_AiArt` — `attachments/Media/SumoOtoshi_MF_AiArt.png` | The woman is visibly active in energetic paired practice, matching body capability, energy, and confidence. |
| W 2603_1 | `Shihonage_MF_Dojo_Photo`, variant A — `attachments/Media/Shihonage_MF_Dojo_Photo__A.png` | Mixed-gender dojo practice supports breaking routine and embodied activity. The calm-copy link is less literal but remains a coherent action-to-reset message. |

No planned media, headline, or primary text is duplicated within either campaign. All components are campaign-compatible. No new tags are introduced.

### Provisional W38 portfolio

- Men: `Mens Ad J`, `M 2607_1`
- Women: `Womens Ad G`, `W 2603_1`

### Confidence and re-evaluation triggers

- **Snapshot data integrity:** high.
- **Rule application:** high.
- **Final W38 decision:** moderate until W37 closes.
- **Growth-quality confidence:** moderate-low because downstream trial and registration evidence is sparse and incomplete.

Re-evaluate if:

- `M 2609_1` receives enough late W37 leads to move below ₪50 CPL; approximately two total W37 leads at present spend would reverse its rule outcome.
- `W 2603_1` receives meaningful late delivery. Replace once a current intended run reaches ₪60 with no leads or continued non-delivery makes the slot operationally useless.
- Late Meta attribution materially changes W37 totals.
- The post-close export changes current-run boundaries or intended flags.
- Grist access resumes and the pending transforms expose a material discrepancy.

# 4. Provisional decision-log entry

This is a draft only. Do not append it to `decision_log.md` until W37 closes and the final refresh confirms the figures.

---

# Plan for 2026-W38 (assessing 2026-W37)

### Weeks

- **Assessed (data) week:** 2026-W37
- **Decision / planned week:** 2026-W38

**Provisional status:** 2026-W37 was still open when this snapshot was captured on 2026-09-16. Finalize only after the post-close refresh.

### Ads active in assessed week (2026-W37)

- Men: Mens Ad J, M 2609_1

| Ad name | Spend | Leads | CPL | Current-run spend | Current-run CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|---:|---:|---:|
| Mens Ad J | ₪118.73 | 4 | ₪29.68 | ₪118.73 | ₪29.68 | ₪3,949.71 | ₪39.11 |
| M 2609_1 | ₪74.04 | 0 | — | ₪163.41 | ₪40.85 | ₪166.40 | ₪41.60 |

- Women: Womens Ad G, W 2603_1

| Ad name | Spend | Leads | CPL | Current-run spend | Current-run CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|---:|---:|---:|
| Womens Ad G | ₪179.73 | 8 | ₪22.47 | ₪396.98 | ₪24.81 | ₪785.88 | ₪35.72 |
| W 2603_1 | ₪0.27 | 0 | — | ₪0.27 | — | ₪609.21 | ₪35.84 |

`Mens Ad B` also delivered ₪7.23 with zero leads, but `Intended_run = false`; it is residual delivery and is excluded from the intended portfolio and current-run construction.

### Ads planned for decision week (2026-W38)

- Men: Mens Ad J, M 2607_1

#### Kept ads

| Name | Reason |
|---|---|
| Mens Ad J | Keep rule 1: W37 spend exceeded ₪20 and CPL was below ₪50. |

#### Reuse ads

| Name | Most recent prior-run CPL | Lifetime CPL | Strength | Reason |
|---|---:|---:|---|---|
| M 2607_1 | ₪43.51 | ₪43.51 | Strong | Top-ranked strong men’s reuse candidate. A complete-new men’s ad launched in W36, so the one W38 replacement slot calls for reuse. |

#### Complete new ads

None.

#### Reshuffle fallbacks

None required because no complete-new men’s ad is proposed.

- Women: Womens Ad G, W 2603_1

#### Kept ads

| Name | Reason |
|---|---|
| Womens Ad G | Keep rule 1: W37 spend exceeded ₪20 and CPL was below ₪50. |
| W 2603_1 | Keep rule 6: W37 and current intended-run spend were both below ₪60. The result is non-delivery, not a negative creative read. |

#### Reuse ads

None; there is no women’s replacement slot.

#### Complete new ads

None.

#### Reshuffle fallbacks

None required because no complete-new women’s ad is proposed.

---

## Portfolio decision

- Keep `Mens Ad J` unchanged.
- Pause `M 2609_1`.
- Activate `M 2607_1` unchanged.
- Keep `Womens Ad G` unchanged.
- Keep `W 2603_1` unchanged.

The provisional 2026-W38 portfolio is:

- Men: `Mens Ad J`, `M 2607_1`
- Women: `Womens Ad G`, `W 2603_1`

---

## Rationale

The intended W37 portfolio spent ₪372.77 for 12 leads at ₪31.06 CPL, versus ₪409.83 for 10 leads at ₪40.98 in completed W36.

`Mens Ad J` and `Womens Ad G` pass keep rule 1 directly. `M 2609_1` triggers rule 5 after spending ₪74.04 with no W37 leads and reaching ₪163.41 in its current run. Its full-run average remains acceptable, so this is a rule-based rotation rather than a conclusion that the creative is intrinsically poor.

`W 2603_1` received only ₪0.27. Because intended-only run identification correctly starts a new run in W37, it remains below the ₪60 replacement threshold and is kept under rule 6.

One men’s replacement slot is open. Because a complete-new men’s ad launched in W36, the slot calls for the top strong reuse candidate. `M 2607_1` ranks first with ₪43.51 prior-run and lifetime CPL.

---

## Constraints check

- Each campaign has exactly two planned ads.
- No media, headline, or primary text is duplicated within a campaign.
- All four actual creatives and source media were visually inspected.
- Image, headline, and primary-text alignment is acceptable for all four ads.
- All components have canonical attachment provenance.
- All tags already exist; no new tags are proposed.
- There is no complete-new ad, so no reshuffle fallback is required.

---

## Data readiness

This entry is based on the locally refreshed Meta snapshot captured around 12:17 IDT and packaged at 12:31:49 IDT. W37 was still open.

The Grist monthly API allowance was exhausted after the W37 Meta rows were written. W37 CPL and performance formulas were recalculated in the packaged export, but `Weekly_Summary` and `Derived_Lifetime_Ad_Conversions` could not be regenerated in Grist. The stale conversion-derived table was not used.

Do not append this entry or implement the W38 switch until the post-close Meta refresh confirms the figures.

---

## What would change this decision at W37 close

- Keep `M 2609_1` if late leads move its final W37 CPL below ₪50.
- Reassess `W 2603_1` if it receives meaningful late spend or if the final intended-run state differs.
- Recalculate all keep rules if late attribution changes lead counts.
- Confirm that `Mens Ad B` remains non-intended residue.
- Replay the pending Grist transforms when API access resumes and compare the regenerated export before logging the final plan.

---

## Confidence level

High confidence in intent identification, run construction, asset integrity, and application of the documented rules to the snapshot. Moderate confidence in the final W38 portfolio because W37 had not closed. Post-lead quality confidence remains limited and should be evaluated separately from the CPL-based weekly decision.

---

End of Plan 2026-W38

# Weekly Decision Log

# 1) Performance summary

## Week structure confirmed

* **Last real logged decision week:** `2026-W13`
* **Previous completed week:** `2026-W13`
* **Latest completed week:** `2026-W14`
* **Decision / planned week:** `2026-W15`

This **is** a valid catch-up situation:

* the latest formal log entry is for **planning `2026-W13` while assessing `2026-W12`**
* two completed data weeks have elapsed since then: **`2026-W13` and `2026-W14`**
* the **same intended portfolio** remained active across both completed weeks:

  * **Men:** `Mens Ad A`, `M 2603_3`
  * **Women:** `Womens Ad P`, `W 2603_4`
* there were small **non-intended residual rows** in `2026-W13`, but no evidence of a real mid-period portfolio change

## Previous completed week — `2026-W13`

| Campaign | Ad          | Weekly spend | Weekly leads | Weekly CPL | Current run spend | Current run CPL | Lifetime spend | Lifetime CPL | Flags                    |
| :------- | :---------- | -----------: | -----------: | :--------- | ----------------: | --------------: | -------------: | -----------: | :----------------------- |
| Men      | M 2603_3    |        45.87 |            0 | —          |            148.29 |           74.14 |         148.29 |        74.14 | low sample; sub-80 spend |
| Men      | Mens Ad A   |       155.74 |            2 | 77.87      |            247.03 |           61.76 |        1072.12 |        42.88 | —                        |
| Women    | W 2603_4    |        59.69 |            0 | —          |            121.38 |           60.69 |         121.38 |        60.69 | low sample; sub-80 spend |
| Women    | Womens Ad P |       141.95 |            0 | —          |            466.76 |           58.34 |         634.69 |        52.89 | low sample               |

## Latest completed week — `2026-W14`

| Campaign | Ad          | Weekly spend | Weekly leads | Weekly CPL | Current run spend | Current run CPL | Lifetime spend | Lifetime CPL | Flags                    |
| :------- | :---------- | -----------: | -----------: | ---------: | ----------------: | --------------: | -------------: | -----------: | :----------------------- |
| Men      | M 2603_3    |       102.42 |            2 |      51.21 |            148.29 |           74.14 |         148.29 |        74.14 | low sample               |
| Men      | Mens Ad A   |        91.29 |            2 |      45.65 |            247.03 |           61.76 |        1072.12 |        42.88 | —                        |
| Women    | W 2603_4    |        61.69 |            2 |      30.84 |            121.38 |           60.69 |         121.38 |        60.69 | low sample; sub-80 spend |
| Women    | Womens Ad P |       139.79 |            3 |      46.60 |            466.76 |           58.34 |         634.69 |        52.89 | —                        |

## Combined two-week hold period — `2026-W13` + `2026-W14`

| Campaign | Ad          | 2w spend | 2w leads | 2w CPL | W14 vs W13 spend Δ | W14 vs W13 leads Δ | Pattern                         | Flags                    |
| :------- | :---------- | -------: | -------: | -----: | -----------------: | -----------------: | :------------------------------ | :----------------------- |
| Men      | M 2603_3    |   148.29 |        2 |  74.14 |              56.55 |                  2 | improvement but still weak      | low sample; modest spend |
| Men      | Mens Ad A   |   247.03 |        4 |  61.76 |             -64.45 |                  0 | improvement                     | —                        |
| Women    | W 2603_4    |   121.38 |        2 |  60.69 |               2.00 |                  2 | improvement; low evidence       | low sample; modest spend |
| Women    | Womens Ad P |   281.74 |        3 |  93.91 |              -2.16 |                  3 | delivery instability / reversal | —                        |

## Key points

* `2026-W13` alone would have pushed toward overreaction: three of the four intended ads had **zero leads**.
* `2026-W14` reversed that picture sharply: **all four intended ads produced leads**, and three of the four were **below 50 CPL**.
* The strongest reversal was in the women’s campaign:

  * `Womens Ad P` went from **141.95 spend / 0 leads** to **139.79 spend / 3 leads / 46.60 CPL**
  * `W 2603_4` went from **59.69 spend / 0 leads** to **61.69 spend / 2 leads / 30.84 CPL**
* `Mens Ad A` remains the clearest men’s anchor: weak `2026-W13`, good `2026-W14`, and strong lifetime evidence.
* `M 2603_3` improved in `2026-W14`, but still missed the keep rule and still has weak run and lifetime evidence.

---

# 2) Summary of current situation

## Key things for the agent to remember

* Treat this as **one catch-up decision for `2026-W15`**, not two ordinary weekly cycles.
* Use **`2026-W14` as the formal assessed week**, but interpret it with explicit reference to:

  * `2026-W13` on its own
  * `2026-W14` on its own
  * the combined `2026-W13` + `2026-W14` hold period
* The intended unchanged portfolio across both completed weeks was:

  * **Men:** `Mens Ad A`, `M 2603_3`
  * **Women:** `Womens Ad P`, `W 2603_4`
* Ignore the tiny non-intended residual rows in `2026-W13` for decision purposes.
* The raw `Weekly_runs` data and lifetime tables are fresher than the exported weekly summary CSVs; do not silently trust stale rollups over fresher raw rows.

## Key things for the human to notice

* The portfolio was **much more volatile across these two weeks than a normal one-week review would reveal**.
* `Womens Ad P` looks weak in the two-week aggregate but strong in the latest week; the right reading is **volatility**, not immediate rejection.
* `W 2603_4` is still **thin evidence**. Its latest week is good, but it is not yet a stable winner.
* `M 2603_3` got a second week and improved, but **not enough** to earn protection.
* The clean exploit move is available in men: **bring back `Mens Ad B`**. It is cooled, historically strong, and component-distinct from `Mens Ad A`.

## Current understanding by category

### Ads

* **Men:** `Mens Ad A` is still a durable baseline. `M 2603_3` does not yet justify another hold week.
* **Women:** `Womens Ad P` remains the strongest ad-level women’s asset, but not stable week to week. `W 2603_4` is promising but underpowered.

### Tags and tag combinations

* Strong recurring men’s exploit space still clusters around:

  * calm / control promises
  * stress / mental-load hooks
  * outside or clean dojo imagery
* Strong women’s assets still cluster around:

  * calm-under-pressure framing
  * meaningful movement / non-force framing
  * visually legible female-centered instruction or calm dojo imagery
* Tag-level conclusions remain useful but **secondary to ad-level and component-level evidence**.

### Headlines

* Strongest headline evidence remains with:

  * `ללמוד לשלוט ברגע`
  * `גוף חזק, ראש רגוע`
  * `לנער את השגרה`
* The current weak men’s ad used one of those strong headlines, which implies the failure is **not headline-only**.

### Texts

* Strongest reusable text evidence remains with:

  * `Everyday Pressure`
  * `Time Out For You (Dad)`
  * `Meaningful Movement`
* `Stable Without Struggle` is not a disaster, but it is notably weaker than the best exploit texts.

### Media

* Strongest lifetime media remain:

  * `Shihonage_MF_Dojo_Photo`
  * `Outside_Sunset_MM_Kaitenage_photo`
  * `Dojo_Instruction_FemalePair`
* `Swariwaza_Kokyuho_Dojo_Photo` is weaker historically, but the latest week gave it a real positive signal.

### Notable headline–text–media combinations

* `Mens Ad A` remains a coherent, strong bundle:

  * `Shihonage_MF_Dojo_Photo`
  * `לנער את השגרה`
  * `Everyday Pressure`
* `Mens Ad B` remains the cleanest eligible exploit return:

  * `Outside_Sunset_MM_Kaitenage_photo`
  * `ללמוד לשלוט ברגע`
  * `Time Out For You (Dad)`
* `Womens Ad P` still looks semantically strong:

  * instructional female line-art image
  * movement/connection headline
  * non-force / balance text
* `W 2603_4` now has one encouraging week, but its evidence base is still too small to call it established.

---

# 3) Key decisions

## Ads to keep

| Campaign | Ad            | Type | Tags                                                                                                                                                          | Brief justification                                                                                                                          |
| -------- | ------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Men      | `Mens Ad A`   | Keep | media: illustration-photo-art / instructional-demonstration; headline: playful, energy-renewal; text: stress/mental-load → calm under pressure, question hook | Latest week CPL **45.65**. Weak `2026-W13` reversed in `2026-W14`. Still the strongest men’s live anchor by lifetime evidence.               |
| Women    | `Womens Ad P` | Keep | media: line-art / dynamic throw; headline: poetic, body capability; text: strength without force, non-violent power, short lines                              | Latest week CPL **46.60**. Two-week view is volatile, but latest week meets keep rule and ad-level evidence remains strong enough to retain. |
| Women    | `W 2603_4`    | Keep | media: dojo photo / soft calm; headline: direct, stress/mental-load, calm under pressure; text: care-load / calm under pressure / checklist                   | Latest week CPL **30.84**. Evidence is still thin, but the written keep rule is met and the latest week is the clearest positive signal yet. |

## Ads generated from existing materials

| Campaign | Planned ad  | Type               | Tags                                                                                                                                    | Brief justification                                                                                                                                                                                          |
| -------- | ----------- | ------------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Men      | `Mens Ad B` | Previously used ad | media: photo-outside / meditative-inspirational; headline: reflective, focus/clarity; text: care-load / calm under pressure / checklist | Best cooled historical winner available. Lifetime CPL **43.23**, last seen **2026-W08**, distinct from `Mens Ad A` on media, headline, and text, and semantically still coherent on actual image inspection. |

## Ads generated with new material

None for `2026-W15`.

Exploit-first is sufficient this week. No novelty is required.

---

# 4) Decision-log entry

# Plan for 2026-W15 (assessing 2026-W14)

### Weeks

* **Assessed (data) week:** 2026-W14
* **Decision / planned week:** 2026-W15

### Ads active in assessed week (2026-W14)

* Men:

| Ad name   |  Spend |   CPL | Lifetime spend | Lifetime CPL |
| --------- | -----: | ----: | -------------: | -----------: |
| Mens Ad A |  91.29 | 45.65 |        1072.12 |        42.88 |
| M 2603_3  | 102.42 | 51.21 |         148.29 |        74.14 |

* Women:

| Ad name     |  Spend |   CPL | Lifetime spend | Lifetime CPL |
| ----------- | -----: | ----: | -------------: | -----------: |
| Womens Ad P | 139.79 | 46.60 |         634.69 |        52.89 |
| W 2603_4    |  61.69 | 30.84 |         121.38 |        60.69 |

### Ads planned for decision week (2026-W15)

* Men:

#### Reuse:

| Name      | Spend |   CPL | Lifetime spend | Lifetime CPL |
| --------- | ----: | ----: | -------------: | -----------: |
| Mens Ad A | 91.29 | 45.65 |        1072.12 |        42.88 |
| Mens Ad B |     — |     — |         951.09 |        43.23 |

#### Reshuffle:

None.

#### New content

None.

* Women:

#### Reuse:

| Name        |  Spend |   CPL | Lifetime spend | Lifetime CPL |
| ----------- | -----: | ----: | -------------: | -----------: |
| Womens Ad P | 139.79 | 46.60 |         634.69 |        52.89 |
| W 2603_4    |  61.69 | 30.84 |         121.38 |        60.69 |

#### Reshuffle:

None.

#### New content

None.

---

## Portfolio decision

* **Men:** keep `Mens Ad A`; replace `M 2603_3` with the cooled historical winner `Mens Ad B`.
* **Women:** keep both current ads.
* **New material:** none for `2026-W15`.

---

## Catch-up note

One weekly decision cycle was skipped.

The portfolio decided for `2026-W13` remained active across **two completed data weeks**: `2026-W13` and `2026-W14`.

This entry therefore uses:

* `2026-W14` as the **formal assessed week**
* `2026-W15` as the **decision / planned week**
* explicit interpretation from:

  * `2026-W13` on its own
  * `2026-W14` on its own
  * the combined `2026-W13` + `2026-W14` hold period

No separate formal entry is written for the skipped cycle.

---

## Rationale (concise)

1. **Use the latest week formally, but do not ignore the hold-period context.**

   * `2026-W13` was highly unstable.
   * `2026-W14` sharply reversed it.

2. **Keep ads that met the latest-week keep rule.**

   * `Mens Ad A`, `Womens Ad P`, and `W 2603_4` all had latest-week CPLs below 50.

3. **Do not protect `M 2603_3`.**

   * It improved in `2026-W14`, but still missed the keep threshold.
   * Its current-run CPL and lifetime CPL are both weak.
   * Its evidence base is too small to justify another hold week.

4. **Exploit the cleanest cooled men’s winner.**

   * `Mens Ad B` is historically strong, inactive long enough, and component-distinct from `Mens Ad A`.

5. **Avoid novelty when exploitation is available.**

   * No new material is needed for `2026-W15`.

---

## Constraints check

* Latest completed week and planned week are explicitly separated.
* This is treated as **one catch-up decision**, not two normal weekly cycles.
* No media, headline, or text is duplicated within the men’s campaign for `2026-W15`.
* No media, headline, or text is duplicated within the women’s campaign for `2026-W15`.
* New-material constraint is satisfied: **0 new ads**.
* `Mens Ad B` satisfies the six-week cooling requirement.
* Planned reused media were checked against actual image content, not tags alone.

---

## Data hygiene / learning notes

* The exported weekly summary CSVs appear stale through `2026-W12`, while raw `Weekly_runs` data and lifetime exports extend to `2026-W14`.
* This catch-up interpretation therefore relied on the fresher raw rows plus lifetime tables.
* Small non-intended residual rows in `2026-W13` were excluded from intent-level evaluation:

  * `M 2603_1` — 3.80 ILS
  * `M 2603_2` — 3.95 ILS
  * `W 2603_3` — 5.37 ILS
* The historical campaign-label inconsistency around `M 2603_2` remains present in the raw data.

---

## What would change this decision next week

* If `Womens Ad P` posts another expensive zero-lead week at meaningful spend, treat the `2026-W14` recovery as noise rather than rebound.
* If `W 2603_4` fails again on normal delivery, stop protecting it on low evidence.
* If `Mens Ad B` underdelivers despite normal spend, move back toward either deeper men’s baselines or a controlled reshuffle.
* If summary exports remain stale relative to raw tables, continue to trust raw rows over lagging rollups.

---

## Confidence level

**Moderate.**

The week structure is clear and the catch-up framing is valid. The main uncertainty is not the portfolio logic; it is the volatility across the two held weeks and the freshness mismatch between stale summary exports and fresher raw rows.

---

End of Plan for 2026-W15

---

# Plan for 2026-W13 (assessing 2026-W12)

### Weeks

* **Assessed (data) week:** 2026-W12
* **Decision / planned week:** 2026-W13

### Ads active in assessed week (2026-W12)

* Men:

| Ad name  | Spend | CPL | Lifetime spend | Lifetime CPL |
| -------- | ----: | --: | -------------: | -----------: |
| M 2603_1 | 64.57 |   — |         253.49 |        63.37 |

* Women:

| Ad name     |  Spend |    CPL | Lifetime spend | Lifetime CPL |
| ----------- | -----: | -----: | -------------: | -----------: |
| Womens Ad P | 185.02 |  37.00 |         352.95 |        39.22 |
| M 2603_2    | 131.34 | 131.34 |         139.81 |       139.81 |

**Data-hygiene note:** `W 2603_3` also appeared in `2026-W12` with `campaign = 0`, missing components, and only `9.00` ILS spend. I am treating it as a stray invalid record rather than a stable campaign asset.

### Ads planned for decision week (2026-W13)

* Men:

#### Reuse

| Name      | Spend | CPL | Lifetime spend | Lifetime CPL |
| --------- | ----: | --: | -------------: | -----------: |
| Mens Ad A |     — |   — |         825.09 |        39.29 |

#### Reshuffle

**M 2603_3**

| Component                         | Spend | CPL | Lifetime spend | Lifetime CPL |
| --------------------------------- | ----: | --: | -------------: | -----------: |
| Outside_Sunset_MM_Kaitenage_photo |     — |   — |        1087.31 |        41.82 |
| ללמוד לשלוט ברגע                  |     — |   — |         880.60 |        40.03 |
| Stable Without Struggle           |     — |   — |         432.89 |        54.11 |

#### New content

None.

* Women:

#### Keep / Reuse

| Name        |  Spend |   CPL | Lifetime spend | Lifetime CPL |
| ----------- | -----: | ----: | -------------: | -----------: |
| Womens Ad P | 185.02 | 37.00 |         352.95 |        39.22 |

#### Reshuffle

**W 2603_4**

| Component                    | Spend | CPL | Lifetime spend | Lifetime CPL |
| ---------------------------- | ----: | --: | -------------: | -----------: |
| Swariwaza_Kokyuho_Dojo_Photo |     — |   — |         952.78 |        63.52 |
| גוף חזק, ראש רגוע            |     — |   — |         855.23 |        38.87 |
| Time Out For You (Mom)       |     — |   — |        1386.80 |        57.78 |

#### New content

None.

---

## Portfolio decision

* **Men:** replace the weak current run with one cooled historical winner and one high-evidence reshuffle.
* **Women:** keep the only clear weekly winner and pair it with a conservative exploitative reshuffle rather than novelty.

---

## Rationale (concise)

1. **Exploit historical winners first.**

   * There is no shortage of proven ads and components.
2. **Do not protect weak probes once they have enough spend to fail.**

   * `M 2603_2` is past that point.
3. **Do not overreact to malformed records.**

   * `W 2603_3` is treated as a data-hygiene issue, not as a learning asset.
4. **Keep the one clean success.**

   * `Womens Ad P` earned that status this week.

---

## Data hygiene / learning notes

* Bring `decision_log.md` back into sync next week; it currently lags the data.
* Fix the campaign assignment for `M 2603_2` in the source system if it is truly a men's ad.
* Investigate why the headline `"משהו חדש לגוף ולראש"` is missing from the headline lifetime export.
* Confirm whether `W 2603_3` is a test placeholder, a failed draft, or a bad export row.

---

## What would change this decision next week

* If **Womens Ad P** falls sharply while its spend remains meaningful, I would stop treating it as an anchor.
* If the **M 2603_3** reshuffle under-delivers despite normal spend, I would revert harder toward the deepest men's baselines.
* If the women reshuffle underperforms while **Womens Ad P** remains strong, I would next test another strong women baseline rather than introduce new content.
* If source-data hygiene remains messy, I would reduce confidence in component-level learning and lean more on ad-level winners.

---

## Confidence level

**Moderately high.**

The main portfolio choices are straightforward. The main uncertainty is not the creative logic; it is the recent metadata quality.

---

End of Plan 2026-W13

---


# Plan for 2026-W12 (assessing 2026-W11)

### Weeks

- **Assessed (data) week:** 2026-W11
- **Decision / planned week:** 2026-W12

### Ads active in assessed week (2026-W11)

- Men:

| Ad name | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| M 2603_1 | 188.92 | 47.23 | 188.92 | 47.23 |
| M 2603_2 | 8.47 | — | 8.47 | — |

- Women:

| Ad name | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| W 2603_1 | 198.61 | 66.20 | 288.60 | 57.72 |
| W 2603_2 | 0.00 | — | 98.24 | 32.75 |

### Ads planned for decision week (2026-W12)

- Men:

#### Reuse:

None.

#### Reshuffle:

None.

#### Keep as-is:

| Name | Weekly spend | Weekly CPL | Run spend | Run CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|---:|---:|
| M 2603_1 | 188.92 | 47.23 | 188.92 | 47.23 | 188.92 | 47.23 |
| M 2603_2 | 8.47 | — | 8.47 | — | 8.47 | — |

- Women:

#### Reuse:

| Name | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| Womens Ad P | 167.93 | 41.98 | 167.93 | 41.98 |

#### Reshuffle:

**W 2603_3**

| Component | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| Shihonage_MF_Dojo_Photo | 824.41 | 39.26 | 824.41 | 39.26 |
| גוף חזק, ראש רגוע | 855.23 | 38.87 | 855.23 | 38.87 |
| Meaningful Movement | 855.23 | 38.87 | 855.23 | 38.87 |

#### New material:

None.

---

## Portfolio decision

- **Men:** keep both current ads.
- **Women:** replace both current ads.
- **New material:** none for 2026-W12.

---

## Rationale

- `M 2603_1` met the primary keep rule in its first meaningful week.
- `M 2603_2` received too little spend to justify replacement.
- `W 2603_1` failed the keep rules after scaling and now appears, from the corrected mapping, to be a weak component combination rather than a pure component failure.
- `W 2603_2` had acceptable run CPL but received zero spend in 2026-W11; under the written rules it is still a replacement, though confidence in the interpretation remains limited.
- The women’s campaign still has enough historical strength to rebuild from existing winners rather than introducing new material.

---

## Constraints check

- Latest completed data week and planned week are explicitly separated.
- No media, headline, or text is repeated within the women’s campaign for 2026-W12.
- At most one ad may contain new material; 2026-W12 contains none.
- The reused ad (`Womens Ad P`) satisfies the six-week cooling rule.
- `W 2603_3` is a new combination of existing materials rather than a repeated historical combination.
- Planned women’s ads were checked against actual image content, not tags alone.

---

## Data hygiene / learning notes

- `ad_components.csv` corrected the current component mappings and materially improved interpretability.
- `M 2603_2` is mislabeled as women’s in component-level exports; campaign identity had to be recovered from the ad name and weekly context.
- `Dojo_Instruction_FemalePair` and `Dynamic_Throw_FF_LineArt` are duplicate image files under different names.
- `Illustrated_Soft_Strength_Female` appears mis-tagged as `Photo - Dojo`.
- Delivery concentration remains a confound: low-spend ads should not be over-interpreted.

---

## What would change this decision next week

- If `M 2603_2` again receives very low spend, it should stop being protected by the low-delivery rule.
- If the rebuilt women’s portfolio again fails despite higher-delivery proven inventory, the next step should be a deliberately designed **new media** probe.
- If `Womens Ad P` underperforms materially on re-entry, confidence in old women’s winners should be downgraded.

---

## Confidence level

- **Men keep decisions:** high.
- **Women replacement decisions:** medium.
- **Interpretation of `W 2603_2`:** low-to-medium because zero delivery makes the signal ambiguous.

---

End of Plan for 2026-W12

---

# Plan for 2026-W11 (assessing 2026-W10)

### Weeks

- **Assessed (data) week:** 2026-W10
- **Decision / planned week:** 2026-W11

### Ads active in assessed week (2026-W10)

- Men:

| Ad name | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| Mens Ad J | 0.00 | — | 1477.06 | 36.93 |
| M 2602_1 | 195.38 | 97.69 | 285.32 | 71.33 |

- Women:

| Ad name | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| W 2603_1 | 89.99 | 45.00 | 89.99 | 45.00 |
| W 2603_2 | 98.24 | 32.75 | 98.24 | 32.75 |

### Ads planned for decision week (2026-W11)

- Men:

#### Reuse:

None.

#### Reshuffle:

**M 2603_1 (proposed)**

| Component | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| Shihonage_MF_Dojo_Photo | 824.41 | 39.26 | 824.41 | 39.26 |
| לנער את השגרה | 1492.07 | 48.13 | 1492.07 | 48.13 |
| Time Out For You (Dad) | 1087.31 | 41.82 | 1087.31 | 41.82 |

**M 2603_2 (proposed)**

| Component | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| Outside_Sunset_MM_Kaitenage_photo | 1087.31 | 41.82 | 1087.31 | 41.82 |
| ללמוד לשלוט ברגע | 880.60 | 40.03 | 880.60 | 40.03 |
| Everyday Pressure | 824.41 | 39.26 | 824.41 | 39.26 |

- Women:

#### Reuse:

| Name | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| W 2603_1 | 89.99 | 45.00 | 89.99 | 45.00 |
| W 2603_2 | 98.24 | 32.75 | 98.24 | 32.75 |

---

## Portfolio decision
---

# Plan for 2026-W10 (assessing 2026-W09)

### Weeks

* **Assessed (data) week:** 2026-W09
* **Decision / planned week:** 2026-W10

### Ads active in assessed week (2026-W09)

* Men: Mens Ad J, M 2602_1
* Women: W 2602_4, W 2026-W06 2

**Incidental delivery (not intentionally run):**

* Womens Ad A

### Ads planned for decision week (2026-W10)

* Men: Mens Ad J, M 2602_1
* Women: W2603_1, W2603_2

---

## Performance Summary (2026-W09)

### Men

**Mens Ad J**

* Weekly CPL ≈ 35.7
* Run CPL ≈ 32.6
* Lifetime CPL ≈ 36.9

Clear success signal.

---

**M 2602_1**

* Weekly CPL ≈ 45
* 2 leads during first week of delivery.

Early probe with acceptable CPL.

---

### Women

**W 2602_4**

* Weekly CPL ≈ 52
* Run spend ≈ 104

Failed primary keep rule (weekly CPL < 50).
Also failed fallback rule (run spend > 80 with CPL > 30).

---

**W 2026-W06 2**

* Spend ≈ 64
* Leads = 0

Originally retained under the “insufficient delivery” rule (spend < 80).
However, overall campaign signal remained weak.

---

**Womens Ad A**

* Spend ≈ 25
* Leads = 1

This ad was **not intentionally run** and had already been rejected in the previous week.
Delivery occurred due to Facebook serving residual impressions.

Decision: **exclude from evaluation**.

---

## Keep Decisions

### Men

* **Mens Ad J retained**

  * Meets primary rule: weekly CPL < 50.

* **M 2602_1 retained**

  * Early probe with acceptable CPL.

---

## Replacement Decisions

### Women

Initial algorithmic recommendation:

* Replace **W 2602_4**
* Retain **W 2026-W06 2** due to insufficient delivery.

However, during review the following reasoning was applied:

1. The women’s campaign has not produced a stable performer.
2. Both ads lacked convincing signal.
3. Replacing both ads accelerates exploration.

Decision:

* **Replace both W 2602_4 and W 2026-W06 2.**

This creates a **full refresh week for the women’s campaign**.

---

## New Ads

### W2603_1

Media
Shihonage_MF_Dojo_Photo__A

Headline
לנער את השגרה

Text
Quiet Space – Bullet Calm

#### Component status

Media: previously used, historically strong (reshuffle)
Headline: previously used, historically strong (reshuffle)
Text: exploratory component (low historical spend)

#### Rationale

This ad combines two historically strong components with a new text variant.

Design goal:

* high-probability engagement hook
* introduce a calmer text concept to probe messaging tone

Conceptual frame:

“shake the routine” + dojo action imagery + calm internal experience.

---

### W2603_2

Media
Dojo_Instruction_FemalePair

Headline
משהו חדש לגוף ולראש

Text
Posture / shoulder strengthening copy (same text previously used in Womens Ad A)

#### Component status

Media: existing component (reshuffle)
Headline: new combination in this context
Text: previously used text component (reshuffle)

#### Rationale

This ad intentionally probes a **different conceptual entry point** from W2603_1.

Frame:

* instruction
* guided learning
* body awareness

The media shows instructor interaction, so the headline emphasizing learning and discovery was chosen to align visually and semantically.

---

## Component Strategy

Two distinct creative hypotheses are being tested:

### Ad W2603_1

Action / emotional reset frame

* dynamic technique image
* “shake up routine” headline
* calm experiential text

---

### Ad W2603_2

Instruction / learning frame

* instructor-student interaction image
* learning-oriented headline
* posture / strengthening message

This structure improves interpretability of results by testing **two clear messaging directions**.

---

## Naming Decisions

New ads named:

W2603_1
W2603_2

Format chosen:

W + YYMM + variant

Example:

W2603_1

Reasons:

* consistent with existing names (e.g., M 2602_1, W 2602_4)
* chronological lexical sorting
* avoids schema drift

Alternative format `W26_03_1` was considered but rejected due to unnecessary complexity.

---

## Deviations from Assistant Recommendations

During planning several recommendations were revised.

### 1. Replacement scope

Assistant recommendation:

* replace only W 2602_4

Final decision:

* replace **both women’s ads**

Reason:

* accelerate exploration due to weak signal.

---

### 2. Ad component pairing

One assistant-proposed combination contained a text that did not exist in the component table.

This was corrected by:

* reusing verified text from Womens Ad A
* selecting a headline consistent with the instructional media.

---

## Operational Notes

Incidental delivery of previously rejected ads occurred (Womens Ad A).

For future analysis cycles it may be useful to apply a heuristic:

Ignore ads with **spend < 30 ILS unless intentionally run**.

This prevents accidental delivery from influencing weekly evaluation.

---

End of Plan for 2026-W10

---


# Plan for 2026-W09 (assessing 2026-W08)

### Weeks

- **Assessed (data) week:** 2026-W08
- **Decision / planned week:** 2026-W09

### Ads active in assessed week (2026-W08)

- Men: Mens Ad B, Mens Ad J
- Women: Womens Ad A, W 2026-W06 1

### Ads planned for decision week (2026-W09)

- Men: Mens Ad J, M 2602_1
- Women: W 2026-W06 1, W 2602_4

---

## Performance Summary (2026-W08)

- Mens Ad J: Weekly CPL below 50 → retained under primary keep rule.
- Mens Ad B: ~70 ILS spend, 0 leads → failed weekly test and did not justify continued delivery.
- W 2026-W06 1: Minimal spend, no meaningful signal → retained due to insufficient delivery.
- Womens Ad A: CPL ≈ 105 → clear underperformance.

---

## Keep Decisions

- Mens Ad J retained (weekly CPL < 50).
- W 2026-W06 1 retained (low spend; no conclusive signal).

---

## Replacement Decisions

### Men

- Mens Ad B replaced.
- New ad: M 2602_1.
  - Text: Everyday Pressure (masculine grammar).
  - Rationale: 
    - Exploit historically strong text component (<50 lifetime CPL) 
    - New combination. 
    - Avoid reuse of cooled components.

### Women

- Womens Ad A replaced.
   - Reshuffle not viable due to:
     - 3‑month full-ad cooling rule.
     - 1‑week component cooling.
     - Only one female-coded media under 50 CPL, currently active in W 2026-W06 1.
    - Therefore, new-media slot used.
  - New ad: W 2602_4.
    - Headline: לנער את השגרה.
    - Text: Everyday Pressure (feminine grammatical variant).
    - Media: Photo_Dojo_MF_Ikkyo_Static.
      - New media
      - Rationale: 
        - Maintain disciplined component threshold (<50 lifetime CPL for headline and text
        - Accept constraint-driven media probe.

---

## Rule Updates

- Implemented 3-month cooling period for full ads before reuse.
- Implemented 1-week cooling period for components of replaced ads.
- Maintained strict <50 CPL threshold for component exploitation.

---

## Strategic Notes

- Constrained by thin high-performing media pool.
  - Future priority: collect additional female-forward, dynamic images to expand eligible reshuffle space.

---

End of Plan for 2026-W09

---

# Plan for 2026-W08 (assessing 2026-W07)

### Weeks

* **Assessed (data) week:** 2026-W07
* **Decision / planned week:** 2026-W08

### Ads active in assessed week (2026-W07)

* **Men:** Mens Ad J, Mens Ad O
* **Women:** W 2026-W06 2, W 2602_3

### Ads planned for decision week (2026-W08)

* **Men:** Mens Ad J, Mens Ad B
* **Women:** W 2026-W06 2, Womens Ad A

---

## Performance notes from 2026-W07

* Mens Ad J: weekly CPL **39.55** (2 leads on 79.11 spend) — still the anchor, but delivery dropped vs 2026-W06.
* Mens Ad O: weekly CPL **112.18** (1 lead on 112.18 spend); run CPL **127.47** at run spend **127.47** → fails keep rules.
* W 2026-W06 2: weekly CPL **46.94** (1 lead on 46.94 spend) → keep (low sample).
* W 2602_3: weekly CPL **70.05** (2 leads on 140.09 spend) → replace per keep rules.

---

## Portfolio decision

* **Men:** Keep Mens Ad J; replace Mens Ad O with **Mens Ad B** (historical performer, inactive ≥6 weeks).
* **Women:** Keep W 2026-W06 2; replace W 2602_3 with **Womens Ad A** (strongest historical performer, inactive ≥6 weeks).

---

## Rationale (priority order)

1. **Exploit historical winners**

   * Mens Ad B has meaningful lifetime delivery (spend **880.60**, CPL **40.03**) and is eligible for reuse.
   * Womens Ad A is the top Women historical asset in the dataset (spend **855.23**, CPL **38.87**) and is eligible for reuse.
2. **Probe uncertainty**

   * Deferred this week; first stabilize portfolios with high-evidence winners.
3. **Stabilize and interpret**

   * Using reused ads reduces variance from new combinations and keeps interpretation cleaner.

---

## Constraints check

* **New-material constraint:** satisfied (0/1 new ads).
* **Creative uniqueness per campaign:** satisfied (no media/headline/text duplicated within Men; none duplicated within Women).
* **Media provenance:** all media are present in `attachments_manifest.json` and stored in `attachments.tar` under their canonical names.
* **Image–text semantic check:** passed (manual inspection of the planned media vs headline/text).

---

End of Plan for 2026-W08

---

# Plan for 2026-W07 (assessing 2026-W06)

### Weeks

* **Assessed (data) week:** 2026-W06
* **Decision / planned week:** 2026-W07

---

### Ads active in assessed week (2026-W06)

* Men:

| Ad name   | Spend | CPL | Lifetime spend | Lifetime CPL |
| --------- | ----- | --- | -------------- | ------------ |
| Mens Ad J |       |     |                |              |
| Mens Ad O |       |     |                |              |

* Women:

| Ad name      | Spend | CPL | Lifetime spend | Lifetime CPL |
| ------------ | ----- | --- | -------------- | ------------ |
| W 2026-W06 1 |       |     |                |              |
| W 2026-W06 2 |       |     |                |              |

---

### Ads planned for decision week (2026-W07)

* Men:

#### Reuse:

| Name      | Spend | CPL | Lifetime spend | Lifetime CPL |
| --------- | ----- | --- | -------------- | ------------ |
| Mens Ad J |       |     |                |              |
| Mens Ad O |       |     |                |              |

* Women:

#### Reuse:

| Name         | Spend | CPL | Lifetime spend | Lifetime CPL |
| ------------ | ----- | --- | -------------- | ------------ |
| W 2026-W06 2 |       |     |                |              |

#### Reshuffle:

**W 2026-W06 3 – Shihonage Reshuffle**

| Component                | Spend | CPL | Lifetime spend | Lifetime CPL |
| ------------------------ | ----- | --- | -------------- | ------------ |
| Shihonage_MF_Dojo_Photo  |       |     |                |              |
| עוצמה, איזון, בטחון עצמי |       |     |                |              |
| Balance, Not Struggle    |       |     |                |              |

---

## Portfolio decision

* Men campaign remains stable with two proven performers.
* Women campaign retains the stronger of the two previous-week ads.
* The underperforming Women ad is replaced with a reshuffle anchored on a top-tier media asset (Shihonage_MF_Dojo_Photo).

---

## Rationale (concise)

* Shihonage_MF_Dojo_Photo is a statistically meaningful asset (≈1000 ILS lifetime spend, CPL ≈43).
* Headline 7 (עוצמה, איזון, בטחון עצמי) is an existing, proven headline.
* Balance, Not Struggle is among the stronger eligible texts.
* The combination has not previously been run together.
* No component duplication within Women this week.
* No reuse of components from the removed ad.

---

## Constraints check

* Week labels explicit and aligned.
* No component duplication within Women campaign.
* No reuse of removed ad components.
* No new material introduced.
* Gender designation respected.

---

End of Plan 2026-W07

---


# Plan for 2026-W06 (assessing 2026-W05)

### Weeks

* **Assessed (data) week:** 2026-W05
* **Decision / planned week:** 2026-W06

### Ads active in assessed week (2026-W05)

* **Men:** Mens Ad J, Mens Ad O, Mens Ad N

| Ad name   |  Spend |   CPL | Lifetime spend | Lifetime CPL |
| --------- | -----: | ----: | -------------: | -----------: |
| Mens Ad J | 181.32 | 25.90 |         762.74 |        40.14 |
| Mens Ad O |  13.47 |     — |          13.47 |            — |
| Mens Ad N |   0.16 |     — |         260.91 |        52.18 |

* **Women:** Womens Ad P, Womens Ad Q, Womens Ad R

| Ad name     | Spend |   CPL | Lifetime spend | Lifetime CPL |
| ----------- | ----: | ----: | -------------: | -----------: |
| Womens Ad P | 81.38 | 81.38 |         167.93 |        41.98 |
| Womens Ad Q | 18.56 |     — |         142.64 |        71.32 |
| Womens Ad R | 96.91 | 96.91 |          96.91 |        96.91 |

### Ads planned for decision week (2026-W06)

* **Men:** Mens Ad J, Mens Ad O

#### Reuse:

| Name      |  Spend |   CPL | Lifetime spend | Lifetime CPL |
| --------- | -----: | ----: | -------------: | -----------: |
| Mens Ad J | 329.85 | 29.99 |         762.74 |        40.14 |
| Mens Ad O |  13.47 |     — |          13.47 |            — |

* **Women:** W 2026-W06 1, W 2026-W06 2

#### Reshuffle:

**W 2026-W06 1**

| Component                   | Spend | CPL | Lifetime spend | Lifetime CPL |
| --------------------------- | ----: | --: | -------------: | -----------: |
| Dojo_Instruction_FemalePair |  1040 |  41 |           1040 |           41 |
| גוף חזק, ראש רגוע           |   855 |  39 |            855 |           39 |
| Meaningful Movement         |   855 |  38 |            855 |           38 |

**W 2026-W06 2**

| Component                   | Spend | CPL | Lifetime spend | Lifetime CPL |
| --------------------------- | ----: | --: | -------------: | -----------: |
| Outside_Sunset_MM_Kaitenage |  1087 |  41 |           1087 |           41 |
| ללמוד לשלוט ברגע            |   880 |  40 |            880 |           40 |
| Time Out For You            |  1087 |  41 |           1087 |           41 |

---

## Portfolio decision

* None of the women ads active in 2026-W05 met keep criteria; both women slots are replaced.
* Replacement strategy prioritizes **exploitation of historical winners at the component level**.
* Two women ads are constructed as reshuffles using only components with strong lifetime performance.

---

## Rationale (concise)

* Multiple women media, headlines, and texts show CPL ≈ 38–41 at meaningful spend and are treated as reliable exploit anchors.
* Recent week-level volatility does not override lifetime evidence.
* Each planned women ad is anchored on a distinct high-performing media asset, with supporting headline and text chosen from other proven components. Gender alignment was enforced at the text level.

---

## Constraints check

* Creative uniqueness per week: **satisfied** (no component reused across ads).
* New-material constraint: **satisfied** (no new media, headline, or text).
* Decision priority order: **satisfied** (exploit > probe > interpret).

---

## What would change this decision next week

* If exploit-based women ads fail to produce leads or show CPL ≥ 50 at meaningful spend, consider uncertainty probes using low-spend components.

---

## Confidence level

* **Men:** high
* **Women:** medium–high

---

End of Plan 2026-W06

---


# Plan for 2026-W05 (assessing 2026-W04)

### Weeks

* **Assessed (data) week:** 2026-W04
* **Decision / planned week:** 2026-W05

### Ads active in assessed week (2026-W04)

* Men: Mens Ad J, Mens Ad N
* Women: Womens Ad P, Womens Ad Q

### Ads planned for decision week (2026-W05)

* Men: Mens Ad J, Mens Ad O
* Women: Womens Ad P, Womens Ad R

---

## Assessment notes (2026-W04)

* Mens Ad J: 148.53 spend / 4 leads (37.13 CPL) - keep.
* Mens Ad N: 53.96 spend / 1 lead (53.96 CPL); run is 260.67 spend at 52.13 CPL - replace.
* Womens Ad P: 86.55 spend / 3 leads (28.85 CPL) - keep.
* Womens Ad Q: 124.08 spend / 2 leads (62.04 CPL) - replace.

---

## Decisions for 2026-W05

* Keep: Mens Ad J; Womens Ad P.
* Replace Mens Ad N with Mens Ad O (existing materials reshuffle): Shihonage_MF_Dojo_Photo__A.png + "ללמוד לשלוט ברגע" + "Everyday Pressure".
* Replace Womens Ad Q with Womens Ad R (existing materials reshuffle): Illustrated_Calm_Poster_Female.png + "גוף חזק, ראש רגוע" + "Quiet Space - Bullet Calm".
* New-material slot: unused this week.

---

End of Plan for 2026-W05

---

# Plan for 2026‑W04 (assessing 2026‑W03)

### Weeks

- **Assessed (data) week:** 2026‑W04
- **Decision / planned week:** 2026‑W03

### Ads active in assessed week (2026‑W03)

- Men: Mens Ad A, Mens Ad N
- Women: Womens Ad N, Womens Ad O

### Ads planned for decision week (2026‑W04)

- Men: Mens Ad J, Mens Ad N
- Women: Womens Ad P, Womens Ad Q

---

### Rationale (concise)

**Men’s portfolio**

* **Mens Ad J** retained as a stable performer with acceptable historical behavior; no evidence of semantic mismatch or fatigue.
* **Mens Ad N** retained to preserve a second, distinct male creative angle; still early but no negative signal warranting replacement.

**Women’s portfolio**

* **Womens Ad P** introduced as a **pure reshuffle of existing materials**. The goal is incremental learning via a new combination while staying inside previously validated semantic space and without consuming the weekly new‑material allowance.

* **Womens Ad Q** introduced as the **single new‑material ad** for the week:
  
  * New media (instructional interaction with clear female agency)
  * New headline: *עוצמה, איזון, ביטחון עצמי*
  * New text: *Meaningful Movement*
    This decision followed a focused reassessment of image-text alignment around the instructional female‑pair media. Earlier runs with that media showed zero leads but insufficient evidence to attribute failure to copy or headline. The new creative is therefore treated explicitly as a controlled probe of **media + message together**, not as a baseline replacement.

---

### Constraints check

* Creative uniqueness preserved within each campaign.
* Exactly **one** ad contains new material (Womens Ad Q).
* Reused assets traceable to existing attachments.

---

### Notes for next review

* Evaluate Womens Ad Q primarily on **delivery and early lead signal** to determine whether the instructional media can work with stronger, competence‑forward messaging.
* Womens Ad P provides a comparison point using only known components.
* Men’s ads provide continuity for week‑over‑week interpretation.

---

End of plan for 2026-W04

---

# Plan for 2026‑W03 (assessing 2026‑W02)

### Weeks

- **Assessed (data) week:** 2026‑W03
- **Decision / planned week:** 2026‑W02

### Ads active in assessed week (2026‑W02)

- Men: Mens Ad A, Mens Ad N
- Women: Womens Ad N, Womens Ad O

### Ads planned for decision week (2026‑W03)

- Men: Mens Ad A, Mens Ad N
- Women: Womens Ad N, Womens Ad O

---

- **Contiguous runs (as of assessed week end):**
  - Mens Ad A: 2025‑W52 → 2026‑W02 (3 weeks)
  - Mens Ad N: 2026‑W02 → 2026‑W02 (1 week)
  - Womens Ad N: 2026‑W02 → 2026‑W02 (1 week)
  - Womens Ad O: 2026‑W02 → 2026‑W02 (1 week)

### What happened in 2026‑W02

- All four ads delivered meaningful spend (≈48-81 ILS), but **lead counts were low everywhere (1-2 leads/ad)**.
- Mens Ad A showed a **weekly CPL spike (80.7)**, but this was based on **1 lead**; its **current-run CPL remains strong (33.8 over 8 leads)**.
- Womens Ad O produced the best weekly CPL (**23.8 on 2 leads**) with clean image-text alignment.

### Decision for 2026‑W03

**Keep all four currently active ads** (no replacements required this week; preserve new‑material budget).

- **Mens Ad A** - Media: `Shihonage_MF_Dojo_Photo__A.png` (attachment_id=27; sha256=6f84d2a4…) - keep due to strong run-level CPL despite noisy week.
- **Mens Ad N** - Media: `Outside_Sunset_MM_Kaitenage_photo__B.png` (attachment_id=28; sha256=ef37e601…) - keep; early signal is good and outside-photo media performs well in lifetime rollups.
- **Womens Ad N** - Media: `Dojo_Instruction_FemalePair.png` (attachment_id=53; sha256=db735aa7…) - keep; early, low-sample run and spend below strong evidence threshold.
- **Womens Ad O** - Media: `Illustrated_Calm_Poster_Female.png` (attachment_id=38; sha256=97ddbb5d…) - keep; strongest weekly CPL in W02.

### Data hygiene / learning notes

- **Tag integrity risk:** at least one media asset appears to have a Media_Style tag inconsistent with the actual image (e.g., a dojo photo tagged as “Illustration - Poster”). Component/tag learning should be treated cautiously until corrected.

### What would change this decision next week

- If delivery collapses (sharp spend/impressions drop) for a baseline ad, consider a controlled reshuffle.
- If tag-based decisions are desired, prioritize fixing obvious Media_Style / Media_Energy tag mismatches first.

---

End of plan for 2026-W03

---

# Plan for 2026‑W02 (assessing 2026‑W01)

### Weeks

- **Assessed (data) week:** 2026‑W02
- **Decision / planned week:** 2026‑W01

### Ads active in assessed week (2026‑W01)

- Men: Mens Ad A, Mens Ad B
- Women: Womens Ad A, Womens Ad D

### Ads planned for decision week (2026‑W02)

- Men: Mens Ad A, Mens Ad N
- Women: Womens Ad N, Womens Ad O

---

### Context and timing

* **Latest completed data week assessed:** 2026-W01
* **Decision week planned:** 2026-W02
* **Ads launched:** Saturday evening

Operational note:

* From **Thursday through Saturday**, before this decision cycle was fully organized, the following ads continued running:
  
  * **Men:** Mens Ad A, Mens Ad B
  * **Women:** Womens Ad A, Womens Ad D

* This overlap is documented to avoid confusion when interpreting partial‑week performance.

---

### Ads running in 2026-W02

* **Men:** Mens Ad A (kept), Mens Ad N (shuffle)
* **Women:** Womens Ad N (shuffle), Womens Ad O (new text)

---

### Evidence considered

* Weekly and run‑level performance from `performance_data.json` for 2026-W01
* Lifetime ad‑level and tag‑level rollups
* Recent delivery behavior and low‑sample constraints

---

### Decisions

**Keep**

* **Mens Ad A** retained as the anchor ad based on strong weekly and run‑level CPL.

**Shuffle (existing materials only)**

* **Mens Ad N**: new combination of existing media, headline, and text.
* **Womens Ad N**: new combination of existing media, headline, and text.

**New material (one ad only)**

* **Womens Ad O**: new headline and new primary text paired with existing illustrated calm poster media.

---

### Rationale

**Mens Ad A (kept, unchanged)**

* Mens Ad A was retained without modification because it is the only ad that met *both* weekly and run‑level performance criteria with sufficient signal.
* Its media, headline, and text have repeatedly delivered low CPL across multiple weeks, making it the most reliable anchor for the men’s campaign.
* No creative changes were introduced here in order to preserve continuity and to ensure that any changes in overall portfolio performance can be attributed to the exploratory ads rather than disruption of the baseline.

**Mens Ad N (shuffle: media + headline + text)**

* Mens Ad N was created as a **pure reshuffle** of existing components rather than a new-material experiment.
* **Media:** `Dojo_Action_LineArt_Male.png` (existing illustrated dynamic throw; acceptable lifetime CPL; no suppression signals).
* **Headline:** "כוח רגוע מבפנים" (existing men’s headline with strong historical performance).
* **Text:** `Mens_Text_CalmStrength_v2` (existing men’s text emphasizing grounded control and calm strength).
* These components were each previously validated in other combinations but had not been paired together.
* This reshuffle explicitly tests *interaction effects* between known components while minimizing risk in a campaign anchored by Mens Ad A.

**Womens Ad N (shuffle: media + headline + text)**

* Womens Ad N serves as the women’s-campaign analogue of Mens Ad N: a low-risk exploratory reshuffle using only existing materials.
* **Media:** `Dojo_Instruction_FemalePair.png` (existing instructional photo; neutral delivery; semantically flexible).
* **Headline:** "תנועה שמרגישה נכון" (existing women’s headline with stable historical CPL).
* **Text:** `Womens_Text_GentlePractice_v1` (existing supportive, non-competitive framing).
* The goal of this reshuffle is to maintain strong semantic alignment while testing a new combination that has not previously been run.
* This ad provides incremental learning without consuming the single weekly allowance for new material.

**Womens Ad O (new text + headline, existing media)**

* Womens Ad O is the **only ad this week containing new material**, consistent with the weekly constraint.

* **Media:** `Illustrated_Calm_Poster_Female.png` (existing illustrated calm poster; low energy; visually distinct; no recent overuse).

* **New headline:** "מרחב שקט לעצמך" (new; hook = stress / mental load; promise = personal calm; tone = reassuring).

* **New text:** `Womens_Text_CalmPermission_v1`
  
  * Opening line: "מקום לנשום. לא צריך למהר"
  
  * Structure: checklist (three parallel bullets)
  
  * Desire bullets:
    
    * 🌿 תנועה רגועה שמכבדת את הגוף
    * 🌿 אימון רך, תומך ולא תחרותי
    * 🌿 מרחב בטוח לעצור רגע בתוך השבוע
  
  * CTA: "לחצי לפרטים ולהתנסות בשיעור היכרות בלי התחייבות"

* This configuration reflects the hypothesis that recent underperformance in the women’s campaign is driven primarily by **copy fatigue** rather than media failure, and that explicitly permissive calm copy is better matched to this visual than instructional imagery.

**Abandoned alternative (documented explicitly)**

* The preferred initial plan was to pair the **Dojo_Instruction_FemalePair** image with a new headline and text.
* This plan was abandoned because the image had already been posted earlier in the same week, violating the creative‑uniqueness rule.
* As a result, Dojo_Instruction_FemalePair was retained only in a shuffled configuration, and the new copy was reassigned to the illustrated calm poster.

Only one ad includes new material, in line with exploration constraints.

---

### What would change this decision next week

* Any ad producing **<50 ILS CPL over ≥3 leads** becomes a keep candidate.
* Sustained **>65 ILS CPL over ≥3 leads** triggers replacement.
* Clear evidence of media-copy mismatch or delivery suppression may trigger media rotation.

---

### Confidence level

**Moderate-high confidence.**

Decisions balance stability with a single, well‑scoped exploratory change under noisy, low‑budget conditions.

---

End of plan for 2026-W02

---

# Plan for 2026‑W01 (assessing 2025‑W052)

### Weeks

- **Assessed (data) week:** 2025‑W52
- **Decision / planned week:** 2026‑W01

### Ads active in assessed week (2025‑W52)

- Men: Mens Ad A, Mens Ad B
- Women: Womens Ad A, Womens Ad J

### Ads planned for decision week (2026‑W01)

- Men: Mens Ad A, Mens Ad B
- Women: Womens Ad A, Womens Ad D

---

### Context

* Latest completed data week in export: **2025-W52**.
* Campaign changes executed late in the week → expected **low volume and noisy CPLs**.

### Active Portfolio (Entering Week)

* **Women:** Womens Ad A, Womens Ad J
* **Men:** Mens Ad A, Mens Ad B
* **Operational note:** Womens Ad J showed **no delivery** (0 spend).

### Evidence Considered

* All active ads were **low sample size (≤2 leads)**; weekly CPLs not considered decisive.

* Lifetime CPL leaders remain:
  
  * Womens Ad A (~37 ILS)
  * Mens Ad B (~38 ILS)

* Tag rollups show **consistent signal** favoring:
  
  * **Photo - Outside** media
  * **Calm** energy

* Womens Ad J exhibited **delivery collapse**, treated as an operational issue rather than a performance signal.

### Decisions

* **Keep** Mens Ad A unchanged.
* **Keep** Mens Ad B unchanged despite weak weekly CPL (treated as noise).
* **Keep** Womens Ad A as baseline women’s creative.
* **Pause / remove** Womens Ad J due to non-delivery.
* **Reactivate** Womens Ad D as second women’s slot.

### Rationale

* Weekly CPL fluctuations interpreted as noise under low volume.
* Portfolio stability prioritized to allow signal accumulation.
* Womens Ad J swap driven by delivery integrity, not by learning conclusions.

### Deferred Actions

* No new creative generation this week.
* No recombination of text/headline/media components.
* Reason: iteration space not exhausted and insufficient evidence to justify exploration.

### Re-evaluation Triggers (Next Week)

* If **Mens Ad A or B** exceed **60-65 ILS CPL over ≥3 leads**, reassess men’s portfolio.
* If **Womens Ad A or D** exceed **~65 ILS CPL over ≥3 leads**, reassess women’s portfolio.
* If delivery collapses again on baseline ads, consider **Media Seed 1**.

---

### Context snapshot

* Men’s and Women’s lead campaigns running at ~30 ILS/day each.

* Portfolio at start of W52 (post-reset):
  
  * **Men:** Mens Ad A, Mens Ad B
  * **Women:** Womens Ad A, Womens Ad D

* W52 is a **full, closed week**. W53 is the upcoming run week.

* Conversion rollups (Has trial / Has registrations / Failures) are now present but still sparse and treated as exploratory telemetry.

---

### Observed performance (W52)

**Men**

* **Mens Ad A:** 2 leads, CPL ≈47 ILS.
* **Mens Ad B:** 1 lead, CPL ≈129 ILS.
* Neither ad reached the ≥3‑lead threshold required for CPL‑based reassessment.
* Mens Ad B’s W52 result is inconsistent with its strong lifetime CPL and treated as week‑level noise.

**Women**

* **Womens Ad A:** 1 lead, CPL ≈76 ILS (above target but below reassessment lead threshold).
* **Womens Ad D:** ~146 ILS spend, **0 leads**, normal delivery.
* Zero‑lead outcome at this spend level is treated as a meaningful negative signal, distinct from high‑CPL noise.

---

### Decision taken

* **Men:** No change.
  
  * Continue **Mens Ad A** and **Mens Ad B** unchanged.

* **Women:** Rotate portfolio.
  
  * Remove **Womens Ad D**.
  * Activate **Womens Ad J** in its original configuration.
  * Keep **Womens Ad A** unchanged.

* No new creatives generated.

* No recombination of text, headline, or media components.

---

### Primary rationale

* Decision rules based on ≥3 leads remain appropriate for high‑CPL evaluation.
* However, sustained **zero‑lead spend (~120-150 ILS) with normal delivery** constitutes a separate failure mode and justifies conservative rotation.
* Mens portfolio does not meet any reassessment trigger.
* Womens Ad D shows insufficient evidence to justify continued budget allocation when proven alternatives exist.
* Action favors portfolio hygiene over exploration.

---

### Alternatives explicitly rejected

* Keeping **Womens Ad D** for another full week: rejected due to zero‑lead spend magnitude.
* Generating new creatives: rejected because historical options are not exhausted.
* Component‑level recombination: rejected due to lack of clean, isolatable signal.

---

### Clarification added to decision rules (implicit)

* Ads that accumulate **~120-150 ILS with zero leads and normal delivery** may be rotated out even if CPL‑over‑≥3‑leads criteria are not met.

---

### What would change this decision next week

* If **Mens Ad A or B** exceed ~60-65 ILS CPL over ≥3 leads, reassess men’s portfolio.
* If **Womens Ad A or J** exceed ~65 ILS CPL over ≥3 leads, reassess women’s portfolio.
* If baseline delivery collapses (suppression or sharp impression drop), consider Media Seed 1.
* If baseline ads stabilize but CPL trends upward across weeks, consider controlled recombination before new creative generation.

---

### Confidence level

**High confidence.**

Decision is conservative, evidence‑aligned, and consistent with stability‑first portfolio management.

---

End of plan for 2026-W01

---

# Plan for 2025‑W52 (assessing 2025‑W51)

### Weeks

- **Assessed (data) week:** 2025‑51
- **Decision / planned week:** 2025‑W52

### Ads active in assessed week (2026‑W51)

- Men: Mens Ad K, Mens Ad M
- Women: Womens Ad M, Womens Ad G

### Ads planned for decision week (2025‑W52)

- Men: Mens Ad A, Mens Ad B
- Women: Womens Ad A, Womens Ad D

---

## Context snapshot

* Men’s and Women’s lead campaigns running at ~30 ILS/day each.

* At start of week, active creatives were:
  
  * **Men:** Mens Ad K, Mens Ad M
  * **Women:** Womens Ad M, Womens Ad G

* W51 data incomplete and treated as provisional.

---

## What changed since last decision

* **Mens Ad K** accumulated ~125 ILS across W50-W51 with **zero leads** (no longer low-sample).
* **Mens Ad M** produced leads but at elevated CPL (≈65 in W50, ≈95 in W51 provisional).
* **Womens Ad M** remained stable but expensive (≈71-73 CPL across W50-W51; 4 total leads).
* **Womens Ad G** produced 1 lead at low CPL in W51, but remains a single-event result.

---

## Decision taken

* **Men:** Remove Mens Ad K and Mens Ad M.
  
  * Activate **Mens Ad A** and **Mens Ad B** in their original configurations.

* **Women:** Remove Womens Ad M.
  
  * Activate **Womens Ad A** and **Womens Ad D** in their original configurations.

* No new creatives generated.

* No recombination of existing components.

---

## Primary rationale

* Recent underperformance is best explained at the **ad level**, not the component level.
* Multiple historically strong creatives are available and currently inactive.
* Evidence does not yet justify exploration or creative novelty.
* This week is treated as a **portfolio reset**, not an iteration or exploration phase.

---

## Alternatives explicitly rejected

* **Recombining components** from Mens K/M or Womens M/G: rejected due to lack of clear component-level signal.
* **Generating new text, headline, or media:** rejected because proven baseline creatives are not exhausted.
* **Keeping Womens Ad G** based on W51 performance: rejected due to single-lead sample size.

---

## What would change this decision next week

* If Mens Ad A or B exceed ~60-65 ILS CPL over ≥3 leads, reassess men’s portfolio.
* If Womens Ad A or D exceed ~65 ILS CPL over ≥3 leads, reassess women’s portfolio.
* If delivery collapses on baseline ads (suppression or sharp impression drop), consider Media Seed 1.
* If baseline ads stabilize but CPL trends upward across weeks, consider controlled recombination or new creative generation.

---

## Confidence level

**High confidence.**

Decision favors evidence-backed stability over novelty in a noisy, low-budget environment.

---

End of plan for 2025-W52

---

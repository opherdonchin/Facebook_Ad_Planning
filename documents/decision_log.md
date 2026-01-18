# Weekly Decision Log

## 2026‑W03 plan (assessed week: 2026‑W02)

### Week disambiguation

- **Assessed week:** 2026‑W02
- **Decision week (planned):** 2026‑W03
- **Contiguous runs (as of assessed week end):**
  - Mens Ad A: 2025‑W52 → 2026‑W02 (3 weeks)
  - Mens Ad N: 2026‑W02 → 2026‑W02 (1 week)
  - Womens Ad N: 2026‑W02 → 2026‑W02 (1 week)
  - Womens Ad O: 2026‑W02 → 2026‑W02 (1 week)

### What happened in 2026‑W02

- All four ads delivered meaningful spend (≈48–81 ILS), but **lead counts were low everywhere (1–2 leads/ad)**.
- Mens Ad A showed a **weekly CPL spike (80.7)**, but this was based on **1 lead**; its **current-run CPL remains strong (33.8 over 8 leads)**.
- Womens Ad O produced the best weekly CPL (**23.8 on 2 leads**) with clean image–text alignment.

### Decision for 2026‑W03

**Keep all four currently active ads** (no replacements required this week; preserve new‑material budget).

- **Mens Ad A** — Media: `Shihonage_MF_Dojo_Photo__A.png` (attachment_id=27; sha256=6f84d2a4…) — keep due to strong run-level CPL despite noisy week.
- **Mens Ad N** — Media: `Outside_Sunset_MM_Kaitenage_photo__B.png` (attachment_id=28; sha256=ef37e601…) — keep; early signal is good and outside-photo media performs well in lifetime rollups.
- **Womens Ad N** — Media: `Dojo_Instruction_FemalePair.png` (attachment_id=53; sha256=db735aa7…) — keep; early, low-sample run and spend below strong evidence threshold.
- **Womens Ad O** — Media: `Illustrated_Calm_Poster_Female.png` (attachment_id=38; sha256=97ddbb5d…) — keep; strongest weekly CPL in W02.

### Data hygiene / learning notes

- **Tag integrity risk:** at least one media asset appears to have a Media_Style tag inconsistent with the actual image (e.g., a dojo photo tagged as “Illustration - Poster”). Component/tag learning should be treated cautiously until corrected.

### What would change this decision next week

- If delivery collapses (sharp spend/impressions drop) for a baseline ad, consider a controlled reshuffle.
- If tag-based decisions are desired, prioritize fixing obvious Media_Style / Media_Energy tag mismatches first.

## Week 2026-W2

### Context and timing

* **Latest completed data week assessed:** 2026-W1
* **Decision week planned:** 2026-W2
* **Ads launched:** Saturday evening

Operational note:

* From **Thursday through Saturday**, before this decision cycle was fully organized, the following ads continued running:

  * **Men:** Mens Ad A, Mens Ad B
  * **Women:** Womens Ad A, Womens Ad D
* This overlap is documented to avoid confusion when interpreting partial‑week performance.

---

### Ads running in 2026-W2

* **Men:** Mens Ad A (kept), Mens Ad N (shuffle)
* **Women:** Womens Ad N (shuffle), Womens Ad O (new text)

---

### Evidence considered

* Weekly and run‑level performance from `performance_data.json` for 2026-W1
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
* Clear evidence of media–copy mismatch or delivery suppression may trigger media rotation.

---

### Confidence level

**Moderate–high confidence.**

Decisions balance stability with a single, well‑scoped exploratory change under noisy, low‑budget conditions.


## Week 2026-W1

### Context

* Latest completed data week in export: **2025-W52.
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

  * **Photo – Outside** media
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

* If **Mens Ad A or B** exceed **60–65 ILS CPL over ≥3 leads**, reassess men’s portfolio.
* If **Womens Ad A or D** exceed **~65 ILS CPL over ≥3 leads**, reassess women’s portfolio.
* If delivery collapses again on baseline ads, consider **Media Seed 1**.

## Week 2025-W52 — 2026-01-02

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
* However, sustained **zero‑lead spend (~120–150 ILS) with normal delivery** constitutes a separate failure mode and justifies conservative rotation.
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

* Ads that accumulate **~120–150 ILS with zero leads and normal delivery** may be rotated out even if CPL‑over‑≥3‑leads criteria are not met.

---

### What would change this decision next week

* If **Mens Ad A or B** exceed ~60–65 ILS CPL over ≥3 leads, reassess men’s portfolio.
* If **Womens Ad A or J** exceed ~65 ILS CPL over ≥3 leads, reassess women’s portfolio.
* If baseline delivery collapses (suppression or sharp impression drop), consider Media Seed 1.
* If baseline ads stabilize but CPL trends upward across weeks, consider controlled recombination before new creative generation.

---

### Confidence level

**High confidence.**

Decision is conservative, evidence‑aligned, and consistent with stability‑first portfolio management.

## Week 2025-W51 2025-12-24

Context snapshot

* Men’s and Women’s lead campaigns running at ~30 ILS/day each.
* At start of week, active creatives were:

  * **Men:** Mens Ad K, Mens Ad M
  * **Women:** Womens Ad M, Womens Ad G
* W51 data incomplete and treated as provisional.

---

## What changed since last decision

* **Mens Ad K** accumulated ~125 ILS across W50–W51 with **zero leads** (no longer low-sample).
* **Mens Ad M** produced leads but at elevated CPL (≈65 in W50, ≈95 in W51 provisional).
* **Womens Ad M** remained stable but expensive (≈71–73 CPL across W50–W51; 4 total leads).
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

* If Mens Ad A or B exceed ~60–65 ILS CPL over ≥3 leads, reassess men’s portfolio.
* If Womens Ad A or D exceed ~65 ILS CPL over ≥3 leads, reassess women’s portfolio.
* If delivery collapses on baseline ads (suppression or sharp impression drop), consider Media Seed 1.
* If baseline ads stabilize but CPL trends upward across weeks, consider controlled recombination or new creative generation.

---

## Confidence level

**High confidence.**

Decision favors evidence-backed stability over novelty in a noisy, low-budget environment.

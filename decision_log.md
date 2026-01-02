# Weekly Decision Log

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

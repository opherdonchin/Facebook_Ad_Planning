# Metrics Definitions (Weekly decisions)

This document defines all performance metrics used in the weekly decision cycle. Its purpose is to ensure consistency over time and prevent silent drift in interpretation.

---

## Time units

### Week

* A **week** is identified by the ISO week label present in `performance_data.json` (e.g., `2026-W01`).
  * Weeks start and end on Thursday. The week definition used by Grist corrects the ISO label for this shift
  * This definition is slightly vague as Thursday overlaps on each week. This can lead to some inconsistencies in reported numberings
    * Try to flag these inconsistencies when you see them.
* Weekly metrics refer only to activity whose timestamps fall within that labeled week.

### This run

* **This run** refers to the most recent *contiguous* sequence of weeks in which an ad had activity.
* A run ends when an end is not selected as one of the 4 for the subsequent week.
* Metrics for “this run” are aggregated across all weeks in that contiguous sequence.

---

## Core delivery metrics

### Exposure

* **Exposure** refers to the Meta-delivered reach or impressions field used in `performance_data.json`.
* Exposure is reported descriptively and is **not** used directly in decision thresholds.

### Spend

* **Spend** is the total amount (ILS) spent by Meta for the ad over the specified period.
* Weekly spend refers to spend within a single week.
* Lifetime spend is the sum of spend across all weeks in which the ad ran.

---

## Lead and cost metrics

### Leads

* **Leads** are counted as successful submissions of the Meta lead form associated with the ad.
* Duplicate submissions by the same individual are counted as separate leads unless explicitly deduplicated upstream.

### Cost per Lead (CPL)

* **CPL** is defined as:

  > `CPL = Spend / Leads`
  >
* CPL is undefined when Leads = 0. In such cases:

  * CPL should be reported as `—` or `NA`
  * Decision logic should fall back to spend-based rules

---

## Lifetime metrics

### Lifetime weeks

* **Lifetime weeks** is the count of distinct weeks in which the ad had any spend or leads.

### Lifetime CPL

* **Lifetime CPL** is computed as:

  > `Total lifetime spend / Total lifetime leads`
  >
* Weeks with zero leads still contribute spend to the numerator.

---

## Outcome metrics (post-lead)

All outcome metrics are derived from downstream data linked to leads.

### Conversion

* A **conversion** indicates that the lead attended an introductory / trial lesson.

### Registration

* A **registration** indicates that the lead registered as a paying student.

### Failure

* A **failure** is any lead that has not converted or registered and has had a status converted to `failed` within the Grist leads database
  * The failed status usually indicates specific sales events and is set manually.
* Leads that have not converted or registered and are not marked failed or not yet failed
* Leads that are registered but marked failed still count as registered
* Outcomes are determined by external algorithms and read as indicated in the tables you receive.

### Percentages

* Conversion %, registration %, and failure % are computed relative to **total lifetime leads** for the ad.
* Percentages always sum to 100%. Be tolerant if this is not the case in the tables. Flag it and go on.

---

## Flags

### Low sample size

* An ad is flagged as **low sample size** when:

  * Lifetime leads < 3, or
  * Weekly leads < 2

### Meta suppression / non-delivery

* An ad is flagged as **suppressed / non-delivered** when:

  * Spend is non-zero but exposure is extremely low, or
  * Spend is near-zero despite the ad being active, or
  * Meta delivery drops sharply without a corresponding decision to pause

These flags are informational but should influence interpretation.

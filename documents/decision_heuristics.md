# Decision Heuristics – Weekly Ad Cycle

This document records stable heuristics used when applying judgment in the weekly decision cycle. It complements explicit numeric thresholds and should change infrequently.

---

## General principles

1. These heuristics are secondary to anything written in the weekly prompt. Instructions or heuristics in the weekly prompt override these instructions and heuristics.
2. Prefer **exploitation over exploration** unless there is no effective exploitation strategy available.
3. Prefer **simplicity over novelty** unless data strongly supports change.

---

## Keep / kill heuristics

### Primary rules (hard constraints)

* Keep ads that meet explicit CPL or spend thresholds defined in the weekly prompt.
* Always keep at least one ad active.

### Fallback selection (when none meet criteria)

When forced to keep a single ad despite poor performance, choose using the following priority order:

1. Lowest lifetime CPL (if lifetime leads ≥ 3)
2. Best recent CPL trend across the current run
3. Strongest evidence for effective tags, headlines, or media
4. Most stable delivery history (least suppression)

If these conflict, prefer the criterion higher on the list.

---

## Interpreting surprising results

Treat a result as **meaningfully surprising** when one or more of the following occur:

* CPL rank order reverses among ads with sufficient leads
* CPL changes sharply week-over-week without a clear delivery explanation
* An ad with historically good performance degrades abruptly
* An ad with poor historical performance shows sustained improvement
* Meta delivery behavior changes independently of creative changes

Surprises should be highlighted even if no immediate decision follows.

---

## Generating new ads

### Controlled variation rule

* Never introduce **new text and new media** in the same ad unless explicitly instructed.
* Successful weeks do not require any novelty
* Moderately successful weeks will generally mean re-combination of known good components or re-introduction of ads that have not been used in a while
* Weeks with poor performance should involve a mix of re-combination, re-use of old material, and novelty.
* ## Choosing what to change
* If recombining (in descending preference order but preference is weak. Make sure choices are varied with some randomness)
  1. New combinations of individual elements that were historically strong
  2. New combinations of tags where the combination has proven successful
  3. New combinations of tags that are historically strong independently
  4. Always respect gender designation. Do not use male adds in female campaigns or vice versa.
* If re-using existing ads
  * Strong historical performers
  * Ads with insufficient evidence
  * Weak historical performers with strong tag combinations or strong tags
* If creating novelty
  * Choose existing elements according to the hierarchy for recombination
  * Choose suggested tags for the novel element that are likely to combine well withthe existing elements or that are strong tags indepedently
  * Respect gender specifications. Do not put male ad components in female campaigns or vice versa.

---

## Be wary using intuition

* When multiple weeks of consistent data contradict intuition
* When clear CPL thresholds are met or violated
* When overriding would reduce comparability across weeks

When no clear guidelines guide you, intuition is an excellent guide.

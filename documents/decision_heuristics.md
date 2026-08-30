# Decision Heuristics – Weekly Ad Cycle

This document records stable heuristics used when applying judgment in the weekly decision cycle. It complements explicit numeric thresholds and should change infrequently.

---

## General principles

1. These heuristics are secondary to anything written in the weekly prompt. Instructions or heuristics in the weekly prompt override these instructions and heuristics.
2. The process is designed to pick short-term winners in a weekly cycle.
3. Use historical reuse when it is strong enough to justify a replacement slot.
4. Use complete new ads regularly enough that the system keeps creating week-one candidates.

---

## Keep / kill heuristics

### Primary rules (hard constraints)

* Keep ads that meet explicit CPL or spend thresholds defined in the weekly prompt.
* Replace ads that meet the replacement thresholds defined in the weekly prompt.
* If both ads in one gender meet the replacement rule, replace both ads in that gender.
* Low delivery after at least 60 ILS of total current-run spend is a replacement signal.

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

## Reuse and new ads

### Reuse candidates

When the weekly prompt calls for reuse, use the same-gender candidate list and sorting rules in the weekly prompt.

Strong reuse means:

1. The ad's most recent prior-run CPL was under 60, or
2. The ad's lifetime CPL was under 50.

Weak reuse means:

1. The ad has produced at least one lead before, and
2. The ad is not strong.

### Complete new ads

Complete new ads contain new media, a new headline, and new primary text designed together.

Build complete new ads in this order:

1. Choose the media concept.
2. Write the headline to match the media.
3. Write the primary text to match the media and headline.
4. Assign existing tags where they fit.
5. Flag proposed new tags explicitly.

### Reshuffle fallbacks

For every complete-new-ad recommendation, provide one same-gender reshuffle fallback.

Build reshuffle fallbacks from existing components that are not already planned for that campaign in the decision week. Select components for:

1. Image-text fit.
2. Prior component performance.
3. Clear difference from the other planned ad in the same campaign.
4. Interpretability of the result.

---

## Be wary using intuition

* When multiple weeks of consistent data contradict intuition
* When clear CPL thresholds are met or violated
* When overriding would reduce comparability across weeks

When no clear guidelines guide you, intuition is an excellent guide.

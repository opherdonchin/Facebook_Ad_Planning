# Decision log format

This document defines the required structure and conventions for entries in `decision_log.md`.

Goals:

- unambiguous week identification
- consistent machine parsing
- fast human scanning
- prevention of implicit temporal wording (“last week”, “this week”, etc.)

## Heading Template

```markdown
# Plan for YYYY-WXX (assessing YYYY-WYY)

### Weeks

- **Assessed (data) week:** YYYY-WYY
- **Decision / planned week:** YYYY-WXX

### Ads active in assessed week (YYYY-WYY)

- Men: <comma-separated ad names>
- Women: <comma-separated ad names>

### Ads planned for decision week (YYYY-WXX)

- Men: <comma-separated ad names>
- Women: <comma-separated ad names>

---

## Section 1

Section 1 content

---

## Section 2

Section 2 content

---

Etc.

---

End of Plan for YYYY-WXX

---
```

## Required heading structure

Every weekly ad decision entry must begin with the following structure.

### Entry title

```markdown
# Plan for YYYY-WXX (assessing YYYY-WYY)
```

- `YYYY-WYY` is the latest completed **data** week being assessed.
- `YYYY-WXX` is the **planned** week being decided (typically `YYYY-WYY + 1`).

---

### Weeks section

```markdown
### Weeks
- **Assessed (data) week:** YYYY-WYY
- **Decision / planned week:** YYYY-WXX
```

These values must match the title exactly.

---

### Ads active in assessed week

```markdown
### Ads active in assessed week (YYYY-WYY)
- Men: 

| Ad name | Spend | CPL | Current-run spend | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|---:|
|          |       |     |                   |                |              |

- Women: <comma-separated ad names>

| Ad name | Spend | CPL | Current-run spend | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|---:|
|          |       |     |                   |                |              |
```

This section records what **actually ran** during the analyzed week, regardless of when the decision was made.

---

### Ads planned for decision week

```markdown
### Ads planned for decision week (YYYY-WXX)
- Men: 

#### Kept ads

| Name | Reason |
|---|---|
| {Ad name} | {Keep rule applied} |

#### Reuse ads

| Name | Most recent prior-run CPL | Lifetime CPL | Strength | Reason |
|---|---:|---:|---|---|
| {Ad name} |       |              | Strong/Weak |        |

#### Complete new ads

**{ New ad name }**

| Component | New / existing | Notes |
|---|---|---|
| Media | New | |
| Headline | New | |
| Text | New | |

#### Reshuffle fallbacks

[One table for each reshuffled fallback ad]

**{ Fallback ad name }**

| Component       | Spend | CPL | Lifetime spend | Lifetime CPL |
|---|---:|---:|---:|---:|
| {Media name}    |       |     |                |              |
| {Headline name} |       |     |                |              |
| {Text name}     |       |     |                |              |

Each complete new ad must have one reshuffle fallback listed for the same gender.

- Women: <comma-separated ad names>

Following the same format as for the men's section

This section records the intended portfolio for the upcoming week.

---

## Recommended sections after the heading

Any of these may appear after the required heading, in any order:

- Portfolio decision
- Rationale (concise)
- Constraints check
- Reuse candidate list by gender
- Data hygiene / learning notes
- What would change this decision next week
- Confidence level

---

## Process-rule notes

Decision-log entries that update the process rather than plan a weekly portfolio may use this heading:

```markdown
# Process rule update - YYYY-MM-DD
```

Use process-rule notes only for changes to the decision process itself. Include:

- reason for the rule change
- evidence reviewed
- rule changes adopted
- when the new rules take effect

Historical weekly decision entries should not be rewritten when the process changes.

---

## End of entry

Finish entry with this easily identified end marker:

```markdown
---

End of Plan YYYY-WXX

---
```

## Prohibited practices

- using “last week”, “this week”, “current week” without explicit `YYYY-WXX` labels
- omitting the assessed or planned week
- combining assessed-week activity and planned-week portfolio in the same list
- copying a non-conforming old entry format instead of following this specification

---

## Canonical sources when something conflicts

- `performance_data.json` is the canonical source for weekly data.
- `decision_log.md` is the canonical record of what was decided.
- this format document is the canonical rule for how decision-log entries are written.

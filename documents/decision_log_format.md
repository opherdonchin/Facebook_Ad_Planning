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

Every decision-log entry must begin with the following structure.

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

| Ad name | Spend | CPL | Lifetime spend | Lifteime CPL |
---------------------------------------------------------
|          |       |     |              |               |

- Women: <comma-separated ad names>

| Ad name | Spend | CPL | Lifetime spend | Lifteime CPL |
---------------------------------------------------------
|          |       |     |              |               |
```

This section records what **actually ran** during the analyzed week, regardless of when the decision was made.

---

### Ads planned for decision week

```markdown
### Ads planned for decision week (YYYY-WXX)
- Men: 

#### Reuse:

| Name      | Spend | CPL | Lifetime spend | Lifetime CPL |
-----------------------------------------------------------
| {Ad name} |       |     |                |              |

#### Reshuffle:

[One table for each reshffuled ad]

**{ New ad name }**

| Component       | Spend | CPL | Lifetime spend | Lifetime CPL |
-----------------------------------------------------------
| {Media name}    |       |     |                |              |
| {Headline name} |       |     |                |              |
| {Text name}     |       |     |                |              |

#### New content

**{ New ad name }**

| Component       | Spend | CPL | Lifetime spend | Lifetime CPL |
-----------------------------------------------------------
| {Media name}    |       |     |                |              |
| {Headline name} |       |     |                |              |
| {Text name}     |       |     |                |              |

**Put new content in bold face and leave Spend / CPL blank**

- Women: <comma-separated ad names>

Following the same format as for the men's section

This section records the intended portfolio for the upcoming week.

---

## Recommended sections after the heading

Any of these may appear after the required heading, in any order:

- Portfolio decision
- Rationale (concise)
- Constraints check
- Data hygiene / learning notes
- What would change this decision next week
- Confidence level

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

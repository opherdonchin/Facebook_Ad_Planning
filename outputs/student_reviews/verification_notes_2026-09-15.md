# Verification & data-quality notes — annual student conversation pack

**Reference date:** 2026-09-15
**Source (read-only):** Grist document *Students*, `vS7JSAjtAG4pPXLAvUNwZe`, org `docs-136683`
**Generator:** `src/annual_student_report.py`
**Nothing in the Grist document was modified.**

---

## 1. Tables and fields used

| Quantity | Table.field |
|---|---|
| Active-student set | `Students.Status = "Active Student"` |
| Practice day | `Sessions.Date` where the student's row id appears in `Sessions.Students_Present` |
| Join date | `Students.Join_Date` |
| Rank + rank date | `Students.Kyu_6 … Kyu_1`, `Students.Dan_1 … Dan_4` (one Date column per rank) |
| Shinsa requirements | `Rank_requirements.Rank`, `.Months`, `.Classes` |
| Eligibility rule | `Students.Eligible` formula |
| Cross-check columns | `Students.Current_Rank`, `.Next_Rank`, `.Date_Last_Test`, `.Months_Since_Last_Test`, `.Sessions_Since_Testing`, `.Total_Session`, `.Required_Months`, `.Required_Classes` |

There is **no separate shinsa/grading table**. Rank history is stored as one date column per rank on the student row, so "previous rank" is simply the next-lowest non-empty rank column.

## 2. Attendance really is one row per practice day

`Sessions` holds **1030 rows with 1030 distinct `Date` values** — a strict 1:1 between rows and dates.
So a practice day for a student is exactly: a `Sessions` row whose `Date` falls in the window and whose
`Students_Present` contains that student.

**Practice days in the last 365 days** =
`COUNT(DISTINCT Sessions.Date)` over `2025-09-16 … 2026-09-15` inclusive (365 calendar days ending on
the reference date), restricted to rows where the student is in `Students_Present`.
`DISTINCT` matters — see anomaly A1.

**Practices/week** = practice days ÷ (365 ÷ 7) = practice days ÷ 52.142857.

**Dojo-wide ceiling:** the dojo recorded **118 practice days** in the window (2.26/week). No student can
exceed that, so the "share of dojo practice days" column is the more interpretable measure of commitment.

## 3. Checks that passed

- **Independent reimplementation vs. Grist's own formulas.** `total_practice_days` was recomputed in SQL
  and compared to `Students.Total_Session`; `practice_days_since_rank` to `Sessions_Since_Testing`;
  `months_since_anchor` to `Months_Since_Last_Test`; rank and next rank to `Current_Rank` / `Next_Rank`;
  eligibility to `Students.Eligible`. **21/21 students match on all six.**
- **Attendance totals reconcile.** Distinct (student, date) pairs in the window belonging to active
  students = **920**, which equals the sum of the per-student counts in the report.
- **Manual attendance audits.** Full date lists pulled and counted by hand for תומר אליהו (13),
  יהונתן שמחון (18), בקר אבו אלגיעאן (8), רואה פרחאת (2), אגן פרחאת (1) — all match.
  Month-by-month breakdowns pulled and summed for עופר דונחין (103), אורן צביאלי (68),
  Zhuoxin Liu (54), סלבה צידן (29) — all match.
- **Rank audits against session records.** The rank dates coincide with real group-shinsa days:
  on **2026-03-17** all six students whose rank date is that day (Zhuoxin Liu, דור ז'ורנו, ערן גבריאלי,
  שלומית צדיק, שפרה פרנס, סלבה צידן) appear in that session's `Students_Present`; on **2025-10-30**
  both Kyu 3 gradings (אלקסיי אוטסיס, יבגני גולדקין) do; on **2024-12-17** אורן צביאלי's Dan 1 does;
  on **2024-02-06** שחר קצב's Dan 1 does. See A5 for the exceptions.
- **Rank-date ordering.** No active student has out-of-order rank dates or a rank recorded without the
  rank below it.
- **Referential integrity.** Every id in every `Students_Present` list resolves to a real `Students` row.
- **No duplicate student names** anywhere in the table.
- **Count reconciliation.** `Status` breakdown across all 131 rows: Active Student 21, Cancelled 107,
  Guest 2, Paused 1, Notification 0. The output has **21 rows**, matching the active criterion exactly.

## 4. Anomalies and data-quality findings

**A1 — Duplicate attendance entry (corrected here).**
`Sessions` row 1015, date **2026-07-07**, lists **סלבה צידן** twice in `Students_Present`. Counted once,
so his window total is **29**, not 30. Grist's own `Total_Session` already de-duplicates, which is why
the report and Grist agree at 272 lifetime days. This is the only such duplicate in the document.

**A2 — Attendance recorded before the Join date.**

| Student | Join date | Practice days before it |
|---|---|---|
| אלקסיי אוטסיס | 2021-11-05 | 5 (2021-10-07, 10-14, 10-21, 10-28, 10-29) |
| יבגני גולדקין | 2021-11-05 | 5 (same dates) |
| בקר אבו אלגיעאן | 2026-04-01 | 1 (2026-03-31) |

Most likely trial practices before formal registration. Because of this, **first recorded practice and
Join date are reported as two separate columns** and never conflated.

**A3 — Three columns default to a value, which can silently create wrong data.**
`Students.Join_Date` and `Sessions.Date` both default to `TODAY()`, and `Students.Status` defaults to
`"Active Student"`. A row created and left unedited therefore gets today's date and lands in the active
set. This does not appear to have produced a visibly wrong row today, but it is the main structural risk
to the active-student count and to join dates.

**A4 — Rank dates that predate joining (not errors, but they change the meaning of "months since rank").**
עופר דונחין holds Dan 1 (2001-07-19) and Dan 2 (2004-01-09) from before his 2015 join date;
דורון שגב's Dan 1 (2024-09-09) predates his 2024-10-24 join date. "Months since rank" for these people
is months since a grading that may have happened elsewhere, not months since a shinsa held here.

**A5 — Rank dates with no matching session, and one grading day the student isn't marked present.**
- **שחר קצב**: Dan 1 is dated **2024-02-06, exactly his Join date**, and Dan 2 follows only ~3.9 months
  later (2024-06-02) against a 30-month requirement. Dan_1 was very likely backfilled with the join date
  rather than a real shinsa date. There is **no `Sessions` row at all on 2024-06-02**.
- **דורון שגב**: Dan 1 dated 2024-09-09 — **no `Sessions` row on that date** either.
- **עופר דונחין**: Dan 4 dated 2025-04-04; a session exists that day but **he is not in its
  `Students_Present`** list.

None of these are contradictions in `Current_Rank` — the rank ladder is internally consistent for every
active student — but they mean three rank dates are not corroborated by the attendance record.

**A6 — Borderline membership cases (left for a human decision, not silently resolved).**
- **יעל בלאסן** is `Paused` but practiced on **2026-09-01**, 14 days before the reference date — by
  behaviour she looks current. She is **excluded** because the criterion used is `Status = "Active Student"`.
- The 2 `Guest` rows have no attendance in the window and are excluded.
- Among `Cancelled` students, the most recent practice is **מארק אידלמן** on 2026-03-31; everyone else
  cancelled last practised over six months ago. No obviously stale cancellation.

**A7 — "Classes" vs. practice days: a genuine unit mismatch in the dojo's own rule.**
`Rank_requirements.Classes` is labelled in *classes*, but the `Eligible` formula compares it to
`Sessions_Since_Testing`, which counts *practice days*. If the dojo ever runs more than one class on a
practice day, the requirement is effectively being enforced in days and is therefore harder to meet than
the label suggests. **Reported, not resolved** — this is a convention question only you can settle.

**A8 — Eligibility has no recency requirement.**
The rule is cumulative since the last shinsa (or since joining). **תומר אליהו** reads *eligible for Kyu 6*
on 34 months and 48 practice days, but he practised only **13 days in the last year**. Formally eligible,
practically a different conversation.

**A9 — Nine of 21 active students have never tested here.** For them the rule anchors on `Join_Date`, so
"months since rank" is blank in the table and the detail section reports "months since joining" instead.

**A10 — `Kyu_2` and `Kyu_1` are typed `Any`, not `Date`**, unlike every other rank column. They are empty
for every one of the 131 students in the document, so nothing is affected today, but a non-date value
entered there would break the date arithmetic in `Date_Last_Test` and `Months_Since_Last_Test`.

**A11 — Missing and stale field values among active students.**
- No `Birthday`: דורון שגב, סלבה צידן, בקר אבו אלגיעאן.
- No `Paid_until`: Zhuoxin Liu, עופר דונחין, אביב ברקובסקי, אגן פרחאת, אילנה בלוך, בקר אבו אלגיעאן,
  רואה פרחאת, רוברט בוקינג.
- `Paid_until` in the past: **יבגני גולדקין, 2026-05-27**.
- No phone and no email: סלבה צידן.

## 5. Ambiguities deliberately left open

1. **Whether `Paused` counts as current** (A6). The report uses `Status = "Active Student"` strictly.
2. **Whether requirements are in classes or practice days** (A7).
3. **Whether the three uncorroborated rank dates are real shinsa dates** (A5).
4. **No next-shinsa date is stated.** The document has no *planned*, *recommended* or *expected* shinsa
   field — only the computed `Eligible` boolean. So the report gives:
   - **eligible now / not yet**, exactly as the dojo rule computes it;
   - the **date the time half of the rule is satisfied** (`rank date + (required months − 1)`), which is
     exactly derivable;
   - the **number of further practice days needed** for the attendance half.
   The attendance half cannot be turned into a date without assuming future attendance, so no date is
   given for it. **No shinsa date anywhere in this pack is inferred from general Aikido practice.**

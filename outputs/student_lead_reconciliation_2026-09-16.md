# Lead–student reconciliation — completed 2026-09-16

## Outcome

Identity links and current-cancellation coverage now reconcile for every non-Guest Student. Full historical state replay remains incomplete because Ying Lin has no recoverable start date or Registration event, and temporary Student pauses are not yet represented as ledger events.

| Integrity measure | Verified result |
|---|---:|
| Leads | 478 |
| Students | 132 |
| Non-Guest students with reciprocal Lead/Student IDs | 130 / 130 |
| Active / Paused / Cancelled / Guest students | 21 / 1 / 108 / 2 |
| Currently cancelled students with `Cancellation_Date` | 108 / 108 |
| Currently cancelled students with a Lead cancellation event | 108 / 108 |
| First Registration events | 129 |
| Return events | 5 |
| Cancellation events | 114 |
| Sales events total | 789 |
| Leads still marked `Pause` | 0 |
| Sales events attached to `Special event` rows | 0 |

The 114 cancellation rows include historical prior cycles, Zhuoxin and Tomer's prior cycles, Ying Lin's known cancellation, and Dor Zourno's future scheduled cancellation. There are **113 cancellations effective on or before 2026-09-16**.

## Membership accounting rule

- The first membership start is `Registration`.
- A start after a prior cancellation is `Return`.
- `Registration + Return` is used for gross membership starts and net active flow.
- Only `Registration` is used for first-time acquisition, campaign conversion, and CAC.
- A person is counted once in unique-student metrics even when they have multiple membership cycles.

This means Levy Shenkar and Meir Kashani each have two membership starts, but each remains one acquired student. The same return treatment is now used for Zhuoxin Liu, Slava Chadin, and Tomer Eliyahu.

## Completed repairs

### Identity and schema

- Added integer `Student_ID` to Leads and `Lead_ID` to Students; cross-document Ref columns are not possible in Grist.
- Added `Cancellation_Date` to Students.
- Added `Return` to the Sales-events vocabulary.
- Created 88 historical legacy Leads for cancelled students, with Registration at first attendance and Cancellation at last attendance.
- Created six historical Leads for current unmatched students and added Interest plus Registration at first class.
- Created and linked Tomer Eliyahu's Lead.
- Created a cancelled Student row for Ying Lin and linked it to Lead 24.
- Kept Guests 128 and 134 excluded.
- Did not merge Student 51 `חן` into modern failed Lead 300 `Chen`; the evidence was only a generic name similarity.

### User-adjudicated records

| Person | Completed treatment |
|---|---|
| Hanwen Liu | Registration 2024-11-12; Cancellation 2025-06-17 |
| Ying Lin | Student created; Cancellation 2025-06-19; Registration date left unknown |
| Zhuoxin Liu | Registration 2023-05-04; Cancellation 2025-06-20; Return 2025-07-29; remains Active |
| Benjamin Deutsch | Registration 2022-11-24; Cancellation 2025-07-15; Lead `Pause` changed to `Failed` under the blanket rule |
| Levy Shenkar | Registration 2020-06-18; Cancellation 2021-08-17; Return 2025-08-19; Cancellation 2025-09-28 |
| Meir Kashani | Registration 2017-03-07; Cancellation 2024-03-14; Return 2025-08-14; Cancellation 2025-12-06; reminder workflow status retained |
| Slava Chadin | Registration 2017-07-18; Cancellation 2024-09-24; Return 2026-01-07; remains Active |
| Tomer Eliyahu | Registration 2023-11-02; Cancellation 2025-04-03; Return 2025-07-10; remains Active |
| Dor Zourno | One Registration retained on 2025-09-02; duplicate removed; Notification 2026-09-14; scheduled Cancellation 2026-10-14; remains Active for now |
| Eran Gavrieli | One Registration retained on 2025-10-21; duplicate removed; Student Join Date aligned to 2025-10-21 |
| Oleg Dolgapolshki | Registration moved to Join Date 2025-08-19 |
| Sophie Fogel | Registration moved to Join Date 2025-10-23 |
| Meydan Kaplan | Registration moved to Join Date 2026-01-29 |
| Naor Nismayam | Student phone corrected to authoritative Lead value `0542110885` |
| Yehonatan Shimshon | Remains Active despite the attendance gap, as directed |

Lead cancellation events were retained as authoritative when they differed from Student action history or last attendance. Last attendance was used only where no Lead cancellation existed.

### Lead workflow cleanup

- Backfilled 52 missing Interest events at the Lead creation date during the initial cleanup.
- Changed all 19 `Pause` Leads to `Failed`.
- Left Lena Elbaz open with the literal `What_next` choice `None` and next-action date 2026-09-17; this records the intended fail-if-no-reply workflow rather than failing her early.
- Left Meir Kashani's reminder workflow intact while his Student status remains Cancelled.
- Deleted all 17 Interest events attached to `Special event` pseudo-leads.
- Kept the 17 Special-event rows for calendar/reference purposes, but excluded them from advertising lead counts.

The allowed no-Interest population is now the 88 generated pre-CRM legacy Leads, pre-CRM Leads 23 Hanwen Liu, 24 Ying Lin, and 36 Benjamin Deutsch, plus the 17 Special-event rows that intentionally have no sales events. The last open-workflow scan surfaced only Lena and Meir, both handled as directed; no named unresolved open Lead remains.

Automated reciprocal-link verification proves the Student → Lead direction for all 130 non-Guest Students. The known Tomer orphan was repaired, and no Registration-bearing Lead without a Student is known, but the final script does not independently assert the inverse Lead → Student rule or re-run the stale-next-action scan. Those checks should be made explicit before treating future runs as a general-purpose validator.

## Summary and advertising rollups

- Rebuilt all 67 past/current Weekly Summary event rows directly from raw Sales events.
- Added `Returned`, `Active Starts`, and net growth calculations.
- Added zero-spend rows for the two past event weeks missing from Weekly Summary; future Dor cancellation is not counted as an actual cancellation yet.
- Corrected the week-to-month formula to use the ISO week represented by each Thursday–Wednesday reporting bucket.
- Updated monthly growth to `Registration + Return - Cancellation`.
- Kept registration rate, campaign conversions, and advertising income based on first Registration only.
- Excluded `Special event` rows from the live ad rollup and synced the corrected rollup to the advertising document. For example, `Mens Ad B` now has 13 real leads rather than 14.

## Known exception and follow-up

Ying Lin's attendance and join date cannot be recovered from the current Students/Sessions data, retained Grist action history, available snapshots, or the older CRM table. Her cancellation on **2025-06-19** is supported, and the note says she returned to China. Her `Join_Date` and Registration event were deliberately left blank rather than assigning a false date.

Meir Kashani has attendance on 2026-01-06 after his authoritative 2025-12-06 cancellation. He remains Cancelled as directed; no third membership cycle was invented.

The one currently Paused Student has no Pause event because Pause/Resume events are not yet part of the ledger vocabulary. Current status is preserved, but that interval cannot yet be replayed from events alone.

## Reproducibility and verification

The repair is encoded in `src/reconcile_membership_history.py` and is idempotent for this reconciled snapshot. Its snapshot-specific IDs and integrity counts must be reviewed before using it after legitimate new records arrive. The advertising transform now explicitly excludes Special-event rows and treats Return as non-acquisition. Automated verification completed with **22 passing tests**.

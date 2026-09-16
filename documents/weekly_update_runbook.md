# Agent runbook: weekly Facebook advertising update

This runbook governs the operational update that prepares data for
`documents/weekly_prompt.md`. The update and the later planning analysis are two
separate stages. Do not start the planning analysis until every gate below has
passed.

## Source-of-truth definitions

- Weekly ad spend and Results come from Meta Ads Manager at **ad level** for the
  exact Thursday-through-Wednesday reporting range.
- The Meta ad account timezone controls those dates. Record it in the update
  notes; do not silently substitute the computer's or dojo's timezone.
- For Instant Form campaigns, one lead means one form submission. Meta's
  `onsite_conversion.lead_grouped` and `lead` action rows are alternate
  representations of that result, not two results to add together.
- The Leads and Sales Events tables are the source for identities, trial
  lessons, registrations, failures, cancellations, and returns. They do not
  replace Ads Manager's attributed weekly Results metric.
- Grist exports and files under `outputs/` are downstream data. They cannot
  independently validate the source values from which they were made.

## 1. Establish the reporting window

1. Identify the assessed Thursday-through-Wednesday range and the following
   decision week.
2. Fetch the Meta ad-account timezone and record it with the exact capture time.
3. State whether Wednesday has ended in the account timezone.
4. If the final account day is still open, label every artifact **provisional**.
   A final report requires another refresh after the account day closes.

The current Meta account uses `America/Los_Angeles`. Consequently, a Wednesday
evening in Israel is still an open Meta reporting day. Verify the account value
on every run rather than assuming it never changes.

## 2. Pre-write safety checks

1. Confirm the working tree and preserve unrelated changes.
2. Confirm that every Grist client is using the configured team-site `server`,
   and perform read-only access checks for the Leads, Students, and ad-tracking
   documents if their site or IDs changed.
3. Run the tests:

   ```bash
   pixi run pytest
   ```

4. Capture the weekly sync as a frozen dry-run snapshot for the exact reporting
   range. The first date must be Thursday and the second must be Wednesday:

   ```bash
   pixi run fetch_weekly_runs \
     --since YYYY-MM-DD --until YYYY-MM-DD \
     --snapshot-out outputs/meta_source_YYYY-MM-DD_YYYY-MM-DD.json \
     --dry-run
   ```

5. Export or inspect Ads Manager at ad level for the same inclusive dates with:
   reporting start, reporting end, ad ID/name, amount spent, Results, result
   indicator, and attribution setting.
6. Capture the API and Ads Manager views within five minutes of each other when
   the week is open.

Do not use `export_meta_weekly_csv.py` as the independent comparison: it shares
the same API client and aggregation function as `fetch_weekly_runs`.

## 3. Mandatory source reconciliation

Compare every intended ad and every ad with residual delivery.

| Check | Closed week | Open/provisional week |
|---|---|---|
| Leads/Results | Must match exactly | Must match exactly at the captured snapshot |
| Spend | Must match within currency rounding | Record both timestamps and explain any accrued-spend difference |
| Dates | Exact Thu-Wed account dates | Same, with the incomplete day identified |
| Metric | Same Results definition and attribution setting | Same |

Also inspect raw API action rows for at least every ad with a nonzero lead count.
If both `onsite_conversion.lead_grouped` and `lead` appear, confirm that the
pipeline selected one according to fallback priority. An exact two-to-one
pipeline/UI pattern is a hard warning for alias double-counting.

If any lead count differs, if aliases disagree, or if a closed-week spend value
has an unexplained difference beyond rounding, stop. Do not write to Grist and
do not prepare recommendations.

## 4. Write and read back

Only after reconciliation passes:

1. Replay the exact validated snapshot, using the same reporting dates used at
   capture time:

   ```bash
   pixi run fetch_weekly_runs \
     --since YYYY-MM-DD --until YYYY-MM-DD \
     --snapshot-in outputs/meta_source_YYYY-MM-DD_YYYY-MM-DD.json
   ```

   A live fetch cannot write to Grist; writes require `--snapshot-in`.
2. In the configured ad-tracking Grist document, open `Weekly_runs`, filter
   `Week` to every Wednesday covered by the validated range, and read the
   affected rows back. Display `Ad`, `Week`, `Spend`, `Leads`, and
   `Intended_run`; retain the filtered export or captured values with the
   validation note.
3. Verify ad name/ID, week, spend, leads, and `Intended_run` against the source
   reconciliation.
4. Verify that each ad has only one database row for the canonical computed
   week. A partial-date row and a Wednesday-end row with the same week label are
   duplicates and must be resolved before transforms run.
5. Set or verify `Intended_run` for intentional ads and identify residual
   delivery explicitly.
6. If read-back differs, stop before downstream processing.

## 5. Update business outcomes and derived files

1. Update Sales Events and the Leads database.
2. Reconcile the lead/student data required by the current task.
3. Run the documented downstream commands:

   ```bash
   pixi run update_ads
   pixi run transform_weekly
   pixi run export_ads
   pixi run package_uploads
   ```

4. Confirm that derived weekly, current-run, lifetime, component, and tag totals
   agree with the corrected `Weekly_runs` rows. A source correction requires
   regenerating every downstream artifact; editing report prose is insufficient.
5. Open the package manifest and verify freshness and required files.

## 6. Analysis and publication gate

Before applying `documents/weekly_prompt.md`, write
`outputs/weekly_source_validation.md` containing:

- reporting range and account timezone;
- capture time and closed/provisional status;
- the per-ad source spend and Results;
- comparison outcome and any explained open-day spend drift;
- tests run and their result;
- Grist read-back result;
- downstream regeneration time.

The planning agent must read this note before evaluating CPL or choosing ads.
`pixi run package_uploads` includes the note in the data bundle and should fail
if it is missing.
Do not append a provisional decision to `documents/decision_log.md`. If the
business must act before Meta's Wednesday closes, clearly identify the decision
as provisional and state what the post-close refresh could change.

## 7. Failure handling

- API or Grist limit: preserve the last validated snapshot, state precisely
  which write or refresh did not occur, and stop dependent work.
- Missing or stale source comparison: produce a missing-information report; do
  not infer that derived data is valid.
- Pipeline defect: separate diagnosis and repair from the live update. Add a
  regression test, run the full relevant suite, establish the historical scope,
  and backfill from primary-source data before regenerating reports.
- Manual correction: record the original value, corrected value, source,
  timestamp, affected weeks, and every downstream artifact regenerated.

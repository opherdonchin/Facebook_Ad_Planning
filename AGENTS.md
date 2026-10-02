# Repository instructions for agents

These instructions apply to every automated agent working in this repository.

## Weekly update work

Before performing any weekly update, read and follow
`documents/weekly_update_runbook.md`. Its source-integrity gates are mandatory.

- Treat a weekly update as an operational data workflow, not permission to
  invent, replace, or patch pipeline code while the update is in progress.
- Use only repository commands documented in the runbook. If a command is
  missing or fails, stop the update, diagnose the failure, and tell the user.
  Make a code change only when the user has asked for the pipeline to be fixed.
- Run the relevant tests before any external write. A dry run is required but
  is not proof that the source metrics are correct.
- Never trust derived exports as an independent check of their own source.
  Reconcile ad-level Meta spend and Results against Ads Manager or another
  primary-source export before writing to Grist or preparing a decision report.
- Meta action names can be aliases. In particular, `lead` and
  `onsite_conversion.lead_grouped` can represent the same Instant Form
  submission and must never be added together.
- Record the exact reporting dates, Meta account timezone, capture time, result
  metric, and whether the final account day was closed at capture time.
- Treat report authority and account-day closure as separate properties. A
  report generated on Wednesday for the Thursday update is an authoritative
  `decision report — early`, not a provisional report. If the user explicitly
  requests an early report, classify it the same way. A report captured after
  the account day closes is an authoritative `decision report — late`; early
  and late decision reports have the same authority, and both must record the
  exact capture time and closure status.
- If an unexplained lead difference exists, or a closed-week spend difference
  exceeds ordinary currency rounding, stop. Do not write data, rebuild derived
  outputs, recommend ad changes, or append to the decision log.
- After a successful write, read the affected rows back from Grist and compare
  them with the validated source before running transforms or packaging files.
- Do not silently treat an unrequested open-week working artifact as an
  authoritative decision report. Reserve `provisional` for such working
  artifacts; use one frozen snapshot consistently throughout each report. An
  authoritative early report may still require a later post-close correction
  or re-evaluation if the source changes materially.

## Weekly planning decisions

Before preparing a weekly review or recommendation, read all of
`documents/weekly_prompt.md`, `documents/decision_heuristics.md`, and the latest
process-rule update in `documents/decision_log.md`. The weekly prompt is the
canonical decision rule when wording differs.

- Apply keep/replace thresholds to each active ad before selecting any
  replacement. Do not preserve an ad merely to keep one incumbent running.
- Count replacement slots separately for men and women; never use one gender's
  recent-new-ad history or candidate list to fill the other gender's slot.
- Historical reuse is not the default. For one replacement slot, recommend a
  complete new ad when that gender had no complete-new launch in the assessed
  week or the completed week immediately before it. Otherwise select the
  highest-ranked strong same-gender reuse candidate; if none is strong,
  recommend a complete new ad.
- For two replacement slots, follow the exact table in `weekly_prompt.md`.
  Depending on recent complete-new history and candidate strength, the result
  may be one new plus one reuse, two strong reuses, one reuse plus one new, or
  two complete new ads.
- A complete new ad means new media, new headline, and new primary text designed
  together, starting from the media concept. Every complete-new recommendation
  must include one same-gender reshuffle fallback.
- Use component reshuffles only as fallbacks for complete-new recommendations;
  do not silently substitute a reshuffle or an old ad because it is easier to
  prepare.
- State the two-week complete-new history for each gender and show the ordered
  reuse-candidate list before filling replacement slots. This evidence is
  required even when the final recommendation is reuse.

## Data and code provenance

- State which existing script or documented command produced every material
  number. Clearly label any one-off calculation.
- Do not silently create a replacement data path when an API limit, missing
  dependency, or stale export interrupts the documented workflow.
- New or changed ingestion logic requires regression tests with representative
  raw source rows, including duplicate aliases, missing fallbacks, disagreement
  between aliases, date boundaries, and zero-lead rows.
- Preserve unrelated user changes. In particular, do not alter workspace or
  editor settings as part of a weekly update.
- When a validated source correction affects metrics quoted in prior decision
  entries, preserve the original entry verbatim as historical evidence. Add a
  short warning banner immediately below its title and point to one current
  correction/re-evaluation note. Do not replace old values or rewrite old
  reasoning as though the corrected information had been available then.
- The current correction note must state the affected weeks, defect, corrected
  source values, decisions whose interpretation materially changes, and the
  current operational recommendation. Clearly distinguish counterfactual
  re-evaluation from what was actually decided and run.

## Grist connections and secrets

- Always construct Grist clients from the profile's `doc_id`, `api_key`, and
  `server`. Never rely on the client's personal-site default.
- Personal documents use `https://docs.getgrist.com`; team/Pro documents use
  the team's own `https://<team>.getgrist.com` subdomain.
- Never place an API key, access token, or password in tracked source, output,
  logs, tests, or documentation. `config.json` is ignored and is the current
  local credential store.
- After a site migration, perform read-only table-list and record-read checks
  for every configured document before allowing writes.

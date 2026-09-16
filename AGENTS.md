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
- If an unexplained lead difference exists, or a closed-week spend difference
  exceeds ordinary currency rounding, stop. Do not write data, rebuild derived
  outputs, recommend ad changes, or append to the decision log.
- After a successful write, read the affected rows back from Grist and compare
  them with the validated source before running transforms or packaging files.
- Do not call an open week final. Keep provisional snapshots separate from the
  post-close refresh and use one frozen snapshot consistently throughout a
  provisional report.

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

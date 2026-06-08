# Facebook Ad Planning

A repository for data and planning history on facebook advertising campaigns. Used primarily for Isshin Aikido in Beer Sheva

Includes (and originallys started as a repository for) a Python tool to export complete Grist documents including all data, formulas, metadata, and file attachments via the Grist API.

## Features

- **Complete Data Export**: Extracts all tables, columns, records, and metadata from Grist documents
- **Formula Preservation**: Captures all formulas with their definitions
- **Attachment Management**: Downloads and organizes file attachments with intelligent naming
- **Structured Output**: Exports to JSON format with organized attachment manifest
- **AI-Ready Structured Tables**: Automatically generates 5 pre-joined CSV tables optimized for AI analysis
- **Multiple Format Support**: Export as CSV (default), Parquet, or both formats
- **Derived Metrics**: Computes weekly, lifetime, and tag-based performance aggregations using DuckDB
- **Component Tracking**: Maintains ad-to-component and component-to-tag relationships
- **Upload Bundle Packaging**: Zips weekly data, creative assets, and planning context into upload-ready bundles
- **SHA256 Verification**: Generates checksums for all downloaded attachments
- **Archive Creation**: Automatically packages attachments into compressed tarball
- **Smart File Naming**: Uses record data (Name, Variant fields) to create meaningful filenames
- **Self-hosted Support**: Works with both Grist Cloud and self-hosted Grist instances

## Installation

### Using Pixi (Recommended)

This project uses [Pixi](https://prefix.dev/docs/pixi/overview) for dependency management:

```bash
# Install pixi if you haven't already
# Visit: https://prefix.dev/docs/pixi/installation

# Install dependencies
pixi install

# Run the script
pixi run run
```

### Using pip

```bash
pip install requests
python export_ads.py
```

## Configuration

1. Copy the example configuration file:
   
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json` with your credentials:
   
   ```json
   {
     "ad_planning": {
       "doc_id": "your_ad_planning_document_id",
       "api_key": "your_api_key",
       "server": "https://docs.getgrist.com"
     },
     "leads": {
       "doc_id": "your_leads_document_id",
       "api_key": "your_api_key",
       "server": "https://docs.getgrist.com",
       "table_id": "Leads",
       "columns": {
         "phone": "Phone",
         "email": "Email",
         "name_en": "Name",
         "name_he": "Name_Hebrew_",
         "date": "Date",
         "campaign": "Campaign",
         "ad_name": "Ad_name",
         "platform": "Platform"
       }
     }
   }
   ```

**Finding your credentials:**

- **Document ID**: Found in your Grist document URL: `https://docs.getgrist.com/doc/YOUR_DOC_ID`
- **API Key**: Generate from your Grist profile settings → API section

For self-hosted Grist instances, change the `server` field to your instance URL.

**Security Note:** The `config.json` file is gitignored and will not be committed to version control. Never commit your API key!

## Syncing Leads into Grist

There are two ways to get leads from Meta into Grist. Both paths use the same matching,
deduplication, and conservative-update logic — they share a common library ([src/lead_utils.py](src/lead_utils.py)).

| | API sync (recommended) | CSV import (fallback) |
|---|---|---|
| **Command** | `pixi run sync_meta_leads` | `pixi run sync_leads <file.csv>` |
| **Lead source** | Meta Graph API (automatic) | CSV downloaded manually from Meta |
| **Setup needed** | Access token + `Meta_lead_id` Grist column | None beyond existing config |
| **When to use** | Routine syncing | Token expired, historical backfill, one-off import |

---

## Automatic Meta Lead Sync (`pixi run sync_meta_leads`)

`pixi run sync_meta_leads` polls the Meta Graph API and syncs new leads directly into Grist,
eliminating the manual CSV download step.

### Token setup

The sync requires a Meta access token with lead-reading permissions.

```bash
# Set the token in your environment (recommended)
export META_ACCESS_TOKEN="EAAxxxxxxxxxxxxx..."

# Or add it to config.json under meta.access_token (less recommended)
```

**Required Meta permissions** (empirical: minimum needed varies by token type and Business Manager setup):
- `leads_retrieval` — read lead data from forms
- `pages_show_list` — enumerate pages
- `pages_read_engagement` — required by some endpoints
- `pages_manage_ads` — required for lead form access in some configurations

> **Lead Access Manager caveat**: In Business Manager environments a separate authorization
> step in Lead Access Manager may be required before any token can read lead data, regardless
> of which permission scopes are granted. If you get `#200 Permission error`, check Lead Access
> Manager first.

**Token lifetime**: User access tokens expire in ~60 days. System user tokens can be configured
to be non-expiring. After expiry, re-generate via Facebook Developer Console and update
`META_ACCESS_TOKEN`.

### Required Grist column

Before running in production, add a `Meta_lead_id` column (Text type) to your Grist Leads table,
then map it in `config.json`:

```json
"leads": {
  "columns": {
    "meta_lead_id": "Meta_lead_id"
  }
}
```

This column is the primary deduplication key. Without it, the sync falls back to phone+email
matching only, which is less reliable. The sync refuses to run without this column unless you
pass `--dry-run` or `--allow-no-meta-id`.

### Optional Grist columns

Add these columns for full audit trail (all are Text type unless noted):

| config key | suggested Grist name | what it stores |
|---|---|---|
| `meta_created_time` | `Meta_created_time` | ISO timestamp from Meta API |
| `meta_ad_id` | `Meta_ad_id` | Numeric Meta ad ID |
| `meta_campaign_id` | `Meta_campaign_id` | Numeric Meta campaign ID |
| `meta_form_id` | `Meta_form_id` | Numeric lead form ID |
| `meta_raw_json` | `Meta_raw_json` | Full raw lead payload (JSON) |
| `imported_at` | `Imported_at` | ISO timestamp when first synced |

### config.json: meta section

```json
"meta": {
  "access_token_env": "META_ACCESS_TOKEN",
  "access_token": "",
  "api_version": "v25.0",
  "form_ids": ["23944636508501947"],
  "lookback_days": 14,
  "ad_id_to_ad_name": {
    "23844000000000001": "Summer Trial - Lead Form 1"
  }
}
```

`ad_id_to_ad_name` is optional — use it when the Meta API does not return `ad_name` for a form.

### Required: dry-run before first production sync

Always run `--dry-run` before the first production sync, especially if there are existing leads
that were imported via CSV. Review the proposed changes and confirm there are no unexpected
phone-normalization merges (two entries being treated as the same person when they are not).

```bash
pixi run sync_meta_leads --dry-run
```

The output will show what would be created, updated, and skipped, with phone/email redacted
by default. For full PII in logs (e.g., when debugging), add `--verbose-pii`.

### Basic usage

```bash
# Standard sync (last 14 days, from config)
pixi run sync_meta_leads

# Backfill from a specific date
pixi run sync_meta_leads --since 2026-01-01

# Extend lookback window
pixi run sync_meta_leads --lookback-days 30

# Single form override
pixi run sync_meta_leads --form-id 23944636508501947

# Full PII in logs (for debugging)
pixi run sync_meta_leads --verbose-pii --dry-run
```

### Idempotency guarantee

A second run with no new leads produces **zero Grist writes** (`leads_updated = 0`,
`leads_created = 0`). The sync uses canonical JSON comparison for `meta_raw_json` and
fill-if-missing semantics for all other fields. Only fields that are blank in Grist are filled;
existing Status, names, Campaign, Ad_name, Platform, and all other manually-entered CRM data
are never overwritten.

### Deduplication logic

1. Match by `meta_lead_id` first (if configured).
2. Fall back to `(normalized_phone, normalized_email)` pair.
3. Leads with only phone or only email (no `meta_lead_id` match) are skipped and logged.
4. In-run duplicates (same lead appearing twice in one batch) are detected and skipped.

### Scheduling

Because the sync handles personal contact information, local scheduling is recommended
over hosted CI/CD:

**Windows Task Scheduler** (run every few hours):
```
Action: Start a program
Program: pixi.exe
Arguments: run sync_meta_leads
Start in: D:\Repositories\Facebook_Ad_Planning
```

**Linux/macOS cron** (every 4 hours):
```
0 */4 * * * cd /path/to/Facebook_Ad_Planning && pixi run sync_meta_leads >> logs/sync.log 2>&1
```

---

## Manual CSV Import (`pixi run sync_leads`)

Use this path when the API token has expired, for historical backfills, or to import a specific
date-range export.

### How to download a CSV from Meta

1. Go to **Facebook Business Center** (business.facebook.com)
2. Navigate to **All tools** → **Instant forms**
3. Click on your instant form → **Download**
4. Choose **"Since last download"** or a custom period → **CSV** format
5. Save to `facebook_exports/`

The file is UTF-16 tab-delimited with columns: `id`, `created_time`, `ad_name`, `campaign_name`, `platform`, `email`, `full_name`, `phone_number`.

### Running the import

```bash
pixi run sync_leads "facebook_exports/your_export.csv"
```

Both sync paths use the same matching, deduplication, and conservative-update logic — a lead
imported by CSV and later seen by the API sync will be recognised as the same person and only
have its missing fields backfilled.

**Example output:**

```
[INFO] Successfully read file with encoding=utf-16, delimiter='\t'
[INFO] Found 46 rows with 16 columns
[NAME COMPLEMENT] Added Hebrew name='גדי אדרי' (English already present 'Gadi Edri').
[DONE] Added 2 new leads.
[DONE] Updated 44 existing leads.
```

## Weekly Workflow

This workflow has two cadences:

- **Daily / several times per day**: sync incoming leads from Facebook Instant Forms into the Leads database.
- **Weekly planning cycle**: update manual summary tables, import weekly ad performance, validate metadata, then run transforms/exports.

### Quick Reference

Complete sequence:

```bash
# Daily (or several times per day): sync leads via Meta API (preferred)
pixi run sync_meta_leads
# Fallback: import a manually downloaded CSV instead
# pixi run sync_leads "facebook_exports/leads_export.csv"

# Weekly manual prep in Leads database:
#   1) Update Sales Events
#   2) Update Weekly Summary (including weekly CPL/cost fields from Ads Manager report)

# Weekly: import ad performance CSV into ad_tracking.Weekly_runs
pixi run update_weekly_runs "facebook_exports/ads_manager_weekly.csv"
# Optional safety check first:
# pixi run update_weekly_runs "facebook_exports/ads_manager_weekly.csv" --dry-run

# Weekly manual QA in ad_tracking before transforms:
#   - Set Weekly_runs.Intended_run for ads that were intentionally active
#   - Ensure every ad in Weekly_runs exists in Ads with correct Campaign (W/M)
#   - Ensure each ad has valid creative/component links and gender-appropriate assignments

# Weekly pipeline after manual prep + QA
pixi run update_ads
pixi run transform_weekly
pixi run export_ads
pixi run package_uploads
```

### Detailed Steps

### Step 1: Daily Lead Sync (repeat during the week)

**Automatic (recommended)**: poll Meta directly via the Graph API:

```bash
pixi run sync_meta_leads
```

**Manual fallback**: download from Facebook Instant Forms and import CSV:

1. Go to **Facebook Business Center** (business.facebook.com)
2. Navigate to **All tools** → **Instant forms**
3. Click on your instant form
4. Click **Download**
5. Choose **"Since last download"** or **"Last 3 months"**
6. Select **CSV** format and save the file to `facebook_exports/`

### Step 2: Sync Leads to Grist

Import the Facebook leads into your Grist Leads table:

```bash
pixi run sync_leads "facebook_exports/your_leads_file.csv"
```

The script will:

- Match leads by phone + email combination
- Add missing Hebrew/English names
- Fill in Campaign, Ad name, and Platform information
- Create new records for new leads
- Report any name mismatches or time gaps

When leads are added to the Leads table, Grist automatically updates its native summary table (`Leads_summary_Ad_name`) which groups leads by ad name and counts conversions.

### Step 3: Weekly Manual Update in Leads Database

Before running the weekly pipeline, manually update the **Leads** document:

1. Update **Sales Events**
2. Update the **Weekly Summary** table (including weekly cost/CPL fields from the Ads Manager report)

This step is currently manual and should be completed before `update_ads`, so ad-level rollups are aligned with latest sales/conversion reality.

### Step 4: Download Weekly Performance CSV from Ads Manager

Export weekly ad performance CSV from Ads Manager and save it to `facebook_exports/`.

The import expects these columns:

- `Ad name`
- `Reporting ends` (format: `YYYY-MM-DD`)
- `Amount spent (ILS)`
- `Results`

### Step 5: Import Weekly Runs to Ad Tracking

```bash
pixi run update_weekly_runs "facebook_exports/ads_manager_weekly.csv"
```

The script writes rows into `Weekly_runs` and can auto-create missing ad names in `Ads` when needed.

### Step 6: Manual Data QA in Ad Tracking (Required)

After importing weekly runs, manually validate in Grist:

1. Set `Weekly_runs.Intended_run` for ads that were intentionally active.
2. Confirm all ads in `Weekly_runs` exist in `Ads` with correct campaign assignment (`W`/`M`).
3. Confirm each ad has complete creative linkage (media/headline/text) and that components match intended gender/campaign usage.

Important: auto-created `Ads` rows from Step 5 only contain ad names, so campaign/creative fields must be filled manually before transforms/exports.

### Step 7: Update Ad Statistics from Leads Rollups

Update the Ads table in the `ad_tracking` document with the latest lead counts and conversion data:

```bash
pixi run update_ads
```

This copies rollup data (total leads, trial lessons, registrations, failed contacts) from the Leads rollup table into `ad_tracking.Ads`.

### Step 8: Generate Derived Metrics

Run transforms to update all derived performance metrics tables in the ad_tracking document:

```bash
pixi run transform_weekly
```

This updates 5 tables:

- `Derived_Weekly_Ad_Metrics` - Weekly performance by campaign and ad
- `Derived_Lifetime_Ad_Metrics` - Lifetime aggregate metrics per ad
- `Derived_Last_Run_Ad_Metrics` - Metrics for most recent contiguous run per ad
- `Derived_Tag_Lifetime_Rollups` - Performance aggregated by creative tags (headlines, text, media, hooks, etc.)
- `Derived_Component_Tags` - Component-to-tag junction table for tracking which tags apply to each media/headline/text

**Note**: These transforms work on the ad_tracking document and are independent of the leads sync. They can be run before or after the export step.

### Step 9: Export Ad Performance Data

Export the current state of your ad tracking database from Grist, including all updated metrics, creative assets, and formulas:

```bash
pixi run export_ads
```

This creates **11 analysis files** in `outputs/`:

**JSON Format (full database):**

- `performance_data.json` - Complete database with all tables, metrics, and formulas
- `attachments_manifest.json` - Metadata for all creative assets (images, videos)
- `attachments.tar` - Archive of all creative files

**CSV Format (AI-optimized, default):**

- `ad_weekly_performance.csv` - Weekly performance by ad (grain: ad × ISO week, including intended-run flag)
- `ad_run_summary.csv` - Last contiguous run metrics per ad
- `ad_lifetime_summary.csv` - Lifetime aggregates per ad
- `ad_components.csv` - Ad-to-component mapping (media, headline, text)
- `component_media_lifetime.csv` - Lifetime aggregates per media component
- `component_headline_lifetime.csv` - Lifetime aggregates per headline component
- `component_text_lifetime.csv` - Lifetime aggregates per text component
- `component_tags.csv` - Component-to-tag relationships (164 rows of tag assignments)

**Optional Parquet Format:**

To export as Parquet instead of CSV:

```bash
pixi run export_ads --format parquet
```

Or export both formats:

```bash
pixi run export_ads --format both
```

The CSV files are pre-joined, structured tables optimized for AI analysis with proper data types and clean column names. See [documents/data_schema.md](documents/data_schema.md) for detailed schema documentation.

### Step 10: Package Weekly Upload Bundles

Create the upload bundles after `export_ads` finishes:

```bash
pixi run package_uploads
```

This validates that all required weekly planning files exist, then creates three zip files in `outputs/`:

- `weekly_upload_data.zip` - structured CSVs plus `performance_data.json`
- `weekly_upload_assets.zip` - `attachments_manifest.json` plus `attachments.tar`
- `weekly_upload_context.zip` - decision log, schema, prompt, and planning reference documents

The command also writes `outputs/weekly_upload_manifest.json` with file paths, sizes, and SHA256 checksums. If any required file is missing, the command stops without creating bundles.

### Step 11: Analyze and Plan (AI-Assisted)

With all data updated, you can now:

1. Upload the three generated zip files together in one batch:
   - `outputs/weekly_upload_data.zip`
   - `outputs/weekly_upload_assets.zip`
   - `outputs/weekly_upload_context.zip`
2. Paste or follow `documents/weekly_prompt.md` so the assistant validates and reads every bundled file before analysis.
3. Use the prompt to:
   - Assess previous week's performance
   - Identify which ads to keep running
   - Decide which ads to replace
   - Plan new creative combinations or generate new content
   - Update the decision log

The weekly_prompt provides detailed guidance on making data-driven decisions while staying within creative constraints (e.g., max one new piece of content per week, no duplicate headlines/text within a campaign).

**Why Structured Files?** The CSV/Parquet tables are pre-joined and optimized for AI analysis, eliminating the need for manual JSON parsing and table reconstruction. They provide clean, typed dataframes with proper relationships already established.

### Summary

Complete weekly workflow in order:

1. Throughout the week: `pixi run sync_meta_leads` (or `pixi run sync_leads "facebook_exports/file.csv"` as fallback)
2. Weekly in Leads DB: manually update Sales Events and Weekly Summary
3. Download weekly Ads Manager performance CSV
4. `pixi run update_weekly_runs "facebook_exports/ads_manager_weekly.csv"` - Import weekly spend/leads into `Weekly_runs`
5. In ad_tracking Grist: manually set `Intended_run` and fix any missing/incorrect ad campaign + creative/component metadata
6. `pixi run update_ads` - Copy lead/conversion rollups from Leads to `ad_tracking.Ads`
7. `pixi run transform_weekly` - Generate derived analytical metrics tables
8. `pixi run export_ads` - Export Grist state to JSON + structured CSV/Parquet files
9. `pixi run package_uploads` - Create upload-ready weekly zip bundles in `outputs/`
10. Analyze data and plan next week's ads using AI + the generated bundles + `weekly_prompt.md`

**See [documents/data_schema.md](documents/data_schema.md) for detailed schema documentation of all exported CSV files.**

## Usage

### Basic Export

```python
from export_ads import GristExtractor

extractor = GristExtractor(DOC_ID, API_KEY)
extractor.save_to_json(
    output_file="performance_data.json",
    download_attachments=True,
    attachments_dir="attachments",
    manifest_file="attachments_manifest.json",
    attachments_tar="attachments.tar"
)
```

### Output Files

`pixi run export_ads` generates:

1. **`outputs/performance_data.json`**: Complete database export including:
   
   - Document metadata
   - All table structures and columns
   - All record data
   - Formula definitions
   - Attachment references

2. **Structured data files** (CSV by default, Parquet optional):
   
   - `outputs/ad_weekly_performance.{csv|parquet}` - Weekly metrics by ad × ISO week
   - `outputs/ad_run_summary.{csv|parquet}` - Last contiguous run per ad
   - `outputs/ad_lifetime_summary.{csv|parquet}` - Lifetime aggregates per ad
   - `outputs/ad_components.{csv|parquet}` - Ad → media/headline/text mapping
   - `outputs/component_media_lifetime.{csv|parquet}` - Lifetime aggregates per media component
   - `outputs/component_headline_lifetime.{csv|parquet}` - Lifetime aggregates per headline component
   - `outputs/component_text_lifetime.{csv|parquet}` - Lifetime aggregates per text component
   - `outputs/component_tags.{csv|parquet}` - Component → tag assignments
   
   See [documents/data_schema.md](documents/data_schema.md) for detailed column descriptions.

3. **`outputs/attachments/`**: Directory containing all downloaded files organized by table

4. **`outputs/attachments_manifest.json`**: Detailed manifest of all attachments including:
   
   - File paths and names
   - SHA256 checksums
   - Source table and record information
   - Original filenames and content types

5. **`outputs/attachments.tar`**: Compressed archive of all attachments

`pixi run package_uploads` validates the weekly planning inputs and creates:

1. **`outputs/weekly_upload_data.zip`**:

   - `performance_data.json`
   - all 8 structured CSV files

2. **`outputs/weekly_upload_assets.zip`**:

   - `attachments_manifest.json`
   - `attachments.tar`

3. **`outputs/weekly_upload_context.zip`**:

   - `documents/decision_log.md`
   - `documents/data_schema.md`
   - `documents/decision_log_format.md`
   - `documents/PROJECT_GUIDE.md`
   - `documents/tag_taxonomy.md`
   - `documents/decision_heuristics.md`
   - `documents/weekly_prompt.md`

4. **`outputs/weekly_upload_manifest.json`**: Manifest with bundle membership, file sizes, and SHA256 checksums

## API Reference

### GristExtractor Class

```python
GristExtractor(doc_id: str, api_key: str, server: str = "https://docs.getgrist.com")
```

**Methods:**

- `get_tables()`: Retrieve all tables in the document
- `get_table_columns(table_id)`: Get column definitions for a table
- `get_table_data(table_id)`: Fetch all records from a table
- `download_attachment(attachment_id, output_dir, desired_stem)`: Download a single attachment
- `extract_attachments_from_records(...)`: Download all attachments from a table
- `extract_full_database(download_attachments, attachments_dir)`: Extract complete database
- `save_to_json(...)`: Main export function that saves everything to files

## File Naming Logic

Attachments are intelligently named using the following pattern:

- Single attachment: `{Name}__{Variant}.ext`
- Multiple attachments: `{Name}__{Variant}__1.ext`, `{Name}__{Variant}__2.ext`, etc.
- Fallback: `{table}_{record_id}.ext` if Name field is empty

File stems are sanitized to remove special characters and ensure filesystem compatibility.

## Requirements

- Python ≥ 3.8
- requests ≥ 2.31.0
- pandas ≥ 2.3.3
- duckdb ≥ 1.4.3 (for transforms)
- ibis-framework ≥ 11.0.0 (for transforms)
- pyarrow ≥ 18.0.0 (only required for Parquet format exports)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Example

After running the export on a Grist document with "Creatives" and "Media" tables:

```
Facebook_Ad_Planning/
└── outputs/
    ├── performance_data.json
    ├── attachments_manifest.json
    ├── attachments.tar
    ├── ad_weekly_performance.csv      # (or .parquet with --format parquet)
    ├── ad_run_summary.csv
    ├── ad_lifetime_summary.csv
    ├── ad_components.csv
    ├── component_media_lifetime.csv
    ├── component_headline_lifetime.csv
    ├── component_text_lifetime.csv
    ├── component_tags.csv
    └── attachments/
        ├── Creatives/
        │   ├── Womens Ad M.png
        │   ├── Mens Ad L.png
        │   └── ...
        └── Media/
            ├── Video_Asset_1.mp4
            └── ...
```

## Troubleshooting

- **Authentication Error**: Verify your API key is correct and has access to the document
- **Missing Attachments**: Ensure attachment IDs are numeric and valid
- **File Name Conflicts**: Duplicate filenames are automatically numbered with `__2`, `__3`, etc.

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## Author

Opher Donchin

---

**Note**: Keep your API keys secure and never commit them to version control.

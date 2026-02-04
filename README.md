# Facebook Ad Planning

A repository for data and planning history on facebook advertising campaigns. Used primarily for Isshin Aikido in Beer Sheva

Includes (and originallys started as a repository for) a Python tool to export complete Grist documents including all data, formulas, metadata, and file attachments via the Grist API.

## Features

- **Complete Data Export**: Extracts all tables, columns, records, and metadata from Grist documents
- **Formula Preservation**: Captures all formulas with their definitions
- **Attachment Management**: Downloads and organizes file attachments with intelligent naming
- **Structured Output**: Exports to JSON format with organized attachment manifest
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

## Syncing Facebook Leads to Grist

### Daily

Updating Facebook leads can be done manually if there are only one or two (which is the usual thing). However, to update a batch, there is a sync tool.

#### Download Facebook Leads

To sync leads from Facebook to your Grist leads table, you first need to download the leads export from Facebook:

1. Go to **Facebook Business Center** (business.facebook.com)
2. Navigate to **All tools** in the left sidebar
3. Find and click on **Instant forms** tool
4. Click on your instant form (e.g., "Leads form 6/6/25")
5. Click the **Download** button
6. Choose download period:
   - **Last 3 months**: Downloads all leads from the past 3 months
   - **Since last download**: Downloads only new leads since your last export
7. Select **CSV** format and download

The downloaded file will be in UTF-16 tab-delimited format with columns like `id`, `created_time`, `ad_name`, `campaign_name`, `platform`, `email`, `full_name`, `phone_number`, etc

### Running the Sync

Once you have the Facebook leads CSV file, sync it to your Grist table:

```bash
pixi run sync_leads "path/to/your/leads_export.csv"
```

The script will:

- Match leads by phone + email combination
- Add missing Hebrew/English names (bilingual complement)
- Fill in Campaign, Ad name, and Platform for matched leads
- Create new lead records for unmatched entries
- Report any name mismatches or time gaps (without overwriting data)

**Example output:**

```
[INFO] Successfully read file with encoding=utf-16, delimiter='\t'
[INFO] Found 46 rows with 16 columns
[NAME COMPLEMENT] Added Hebrew name='גדי אדרי' (English already present 'Gadi Edri').
[DONE] Added 2 new leads.
[DONE] Updated 44 existing leads.
```

## Weekly Workflow

This is the complete weekly process for keeping the Grist database up to date with Facebook ad performance and planning new ad campaigns.

### Quick Reference

The complete sequence with commands:

```bash
# 1. Update Weekly run data from Facebook
# This is done manually but could probably be updated
# Update the Weekly Runs table in the Ad tracking database in Grist with this weeks numbers

# 1. Update ad stats
pixi run update_ads
#    → Copies lead counts from Leads summary to Ads table
#    → Reports: "Rows to update: X" → "Updated Ad tracking-Ads from Leads rollup."

# 2. Generate derived metrics
pixi run transform_weekly
#    → Updates 4 analytical tables in ad_tracking document
#    → Reports: "Synced X rows to [table_name]" for each table

# 3. Export ad data
pixi run export_ads
#    → Creates: performance_data.json, attachments_manifest.json, attachments.tar
#    → Reports: "Exported X tables, Y total records, Z attachments"


# 4. AI-assisted analysis and planning
#    → Upload exported files + decision_log.md to AI assistant
#    → Follow weekly_prompt.md to analyze and plan next week's ads
```

### Detailed Steps

### Step 1: Download Facebook Leads

Download the latest leads from Facebook Ads Manager:

1. Go to **Facebook Business Center** (business.facebook.com)
2. Navigate to **All tools** → **Instant forms**
3. Click on your instant form
4. Click **Download**
5. Choose **"Since last download"** or **"Last 3 months"**
6. Select **CSV** format and save the file

Save the downloaded CSV to the `facebook_exports/` directory.

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

### Step 3: Update Ad Statistics

Update the Ads table in the ad_tracking document with the latest lead counts and conversion data:

```bash
pixi run update_ads
```

This copies lead rollup data (total leads, trial lessons, registrations, failed contacts) from the Leads summary table into the Ads table for performance tracking.

### Step 4: Export Ad Performance Data

Export the current state of your ad tracking database from Grist, including all updated metrics, creative assets, and formulas:

```bash
pixi run export_ads
```

This creates three files needed for analysis:

- `performance_data.json` - Complete database with all tables, metrics, and formulas
- `attachments_manifest.json` - Metadata for all creative assets (images, videos)
- `attachments.tar` - Archive of all creative files

### Step 5: Generate Derived Metrics

Run transforms to update all derived performance metrics tables in the ad_tracking document:

```bash
pixi run transform_weekly
```

This updates:

- `weekly_metrics_prod` - Weekly performance by campaign and ad
- `lifetime_ad_metrics_prod` - Lifetime aggregate metrics per ad
- `last_contiguous_run_ad_metrics_prod` - Metrics for current ad runs
- `tag_lifetime_rollups_prod` - Performance aggregated by creative tags (headlines, text, media, hooks, etc.)

**Note**: These transforms work on the ad_tracking document and are independent of the leads sync. They can be run before or after the export step.

### Step 6: Analyze and Plan (AI-Assisted)

With all data updated, you can now:

1. Upload the three export files (`performance_data.json`, `attachments_manifest.json`, `attachments.tar`) to your AI assistant
2. Also upload `documents/decision_log.md` for historical context
3. Follow the prompts in `documents/weekly_prompt.md` to:
   - Assess previous week's performance
   - Identify which ads to keep running
   - Decide which ads to replace
   - Plan new creative combinations or generate new content
   - Update the decision log

The weekly_prompt provides detailed guidance on making data-driven decisions while staying within creative constraints (e.g., max one new piece of content per week, no duplicate headlines/text within a campaign).

### Summary

Complete weekly workflow in order:

1. Download Facebook leads CSV manually from Facebook Ads Manager
2. `pixi run sync_leads "facebook_exports/file.csv"` - Import leads to Grist
3. `pixi run update_ads` - Copy lead stats from Leads summary to Ads table
4. `pixi run export_ads` - Export current Grist state for analysis
5. `pixi run transform_weekly` - Generate derived analytical metrics
6. Analyze data and plan next week's ads using AI + `weekly_prompt.md`

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

The script generates:

1. **`performance_data.json`**: Complete database export including:

   - Document metadata
   - All table structures and columns
   - All record data
   - Formula definitions
   - Attachment references
2. **`attachments/`**: Directory containing all downloaded files organized by table
3. **`attachments_manifest.json`**: Detailed manifest of all attachments including:

   - File paths and names
   - SHA256 checksums
   - Source table and record information
   - Original filenames and content types
4. **`attachments.tar` or `attachments.tar.gz`**: Compressed archive of all attachments

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

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Example

After running the export on a Grist document with "Creatives" and "Media" tables:

```
Facebook_Ad_Planning/
├── performance_data.json      # Complete data export
├── attachments_manifest.json  # Attachment metadata
├── attachments.tar            # Compressed attachments
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

# Facebook Ad Planning

A Python tool to export complete Grist documents including all data, formulas, metadata, and file attachments via the Grist API.

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
python facebook_ad_planning.py
```

## Configuration

1. Copy the example configuration file:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json` with your credentials:
   ```json
   {
     "doc_id": "your_document_id",
     "api_key": "your_api_key",
     "server": "https://docs.getgrist.com"
   }
   ```

**Finding your credentials:**
- **Document ID**: Found in your Grist document URL: `https://docs.getgrist.com/doc/YOUR_DOC_ID`
- **API Key**: Generate from your Grist profile settings → API section

For self-hosted Grist instances, change the `server` field to your instance URL.

**Security Note:** The `config.json` file is gitignored and will not be committed to version control. Never commit your API key!

## Usage

### Basic Export

```python
from facebook_ad_planning import GristExtractor

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

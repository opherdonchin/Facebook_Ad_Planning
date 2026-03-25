# Structured Data Schema

This document describes the schema for the structured CSV/Parquet files exported by the `export_ads` command. These files are generated from the Grist ad tracking database and optimized for AI-assisted analysis.

## Files Overview

Eight tables are exported with pre-joined relationships:

**Tabular weekly files**

1. **ad_weekly_performance.csv** - Weekly metrics per ad
2. **ad_run_summary.csv** - Last contiguous run metrics per ad
3. **ad_lifetime_summary.csv** - Lifetime aggregates per ad
4. **ad_components.csv** - Ad-to-component mapping
5. **component_media_lifetime.csv** - Lifetime aggregates per media component
6. **component_headline_lifetime.csv** - Lifetime aggregates per headline component
7. **component_text_lifetime.csv** - Lifetime aggregates per text component
8. **component_tags.csv** - Component-to-tag relationships

**Non-tabular weekly files**

9. **performance_data.json**
10. **attachments_manifest.json**
11. **attachments.tar**
12. **decision_log.md**

---

## Detailed description of files

---

### 1. ad_weekly_performance.csv

**Grain:** One row per ad × ISO week

Weekly performance metrics for each ad, aggregated by week.

#### Columns

| Column      | Type           | Description                                                  | Example Values             |
| ----------- | -------------- | ------------------------------------------------------------ | -------------------------- |
| `iso_week`  | string         | ISO week identifier (YYYY-WXX format)                        | `2026-W05`, `2025-W52`     |
| `campaign`  | string         | Campaign identifier (W=Women, M=Men)                         | `W`, `M`                   |
| `ad_name`   | string         | Human-readable ad name                                       | `Womens Ad A`, `Mens Ad B` |
| `spend`     | float          | Amount spent in ILS for this week                            | `115.64`, `80.59`          |
| `leads`     | int            | Number of leads generated this week                          | `3`, `0`, `5`              |
| `cpl`       | float or empty | Cost per lead (spend/leads), null if no leads                | `38.55`, null              |
| `intended_run` | boolean     | Whether the ad was intentionally run that week               | `true`, `false`            |

#### Notes

- ISO weeks are sourced directly from Grist's formula column (column `A` in `Weekly_runs` table)
- Empty `cpl` values indicate weeks with no leads (divide by zero)
- `intended_run` is sourced from `Weekly_runs.Intended_run`, so intended ads with zero delivery still remain marked
- ~118 rows covering historical data from June 2025 through February 2026

#### Example Row

```csv
iso_week,campaign,ad_name,spend,leads,cpl,intended_run
2025-W25,W,Womens Ad A,115.64,3,38.546667,true
```

---

### 2. ad_run_summary.csv

**Grain:** One row per ad (showing last contiguous run only)

Metrics for the most recent contiguous run of each ad. A "run" is a sequence of consecutive weeks with spend, separated by gaps of more than 7 days.

#### Columns

| Column           | Type           | Description                          | Example Values |
| ---------------- | -------------- | ------------------------------------ | -------------- |
| `campaign`       | string         | Campaign identifier (W=Women, M=Men) | `W`, `M`       |
| `ad_name`        | string         | Human-readable ad name               | `Womens Ad A`  |
| `run_start_week` | string         | ISO week when last run started       | `2025-W52`     |
| `run_end_week`   | string         | ISO week when last run ended         | `2026-W01`     |
| `weeks_in_run`   | int            | Number of weeks in this run          | `2`, `5`       |
| `run_spend`      | float          | Total spend during this run (ILS)    | `185.85`       |
| `run_leads`      | int            | Total leads during this run          | `3`            |
| `run_cpl`        | float or empty | Cost per lead for this run           | `61.95`        |

#### Notes

- Only the **most recent** contiguous run is captured per ad
- Run identification logic uses 7-day gap detection in `transforms.py`
- ~31 rows (one per ad in the system)

#### Example Row

```csv
campaign,ad_name,run_start_week,run_end_week,weeks_in_run,run_spend,run_leads,run_cpl
W,Womens Ad A,2025-W52,2026-W01,2,185.85,3,61.95
```

---

### 3. ad_lifetime_summary.csv

**Grain:** One row per ad

Lifetime aggregate metrics for each ad since first run.

#### Columns

| Column            | Type           | Description                          | Example Values |
| ----------------- | -------------- | ------------------------------------ | -------------- |
| `campaign`        | string         | Campaign identifier (W=Women, M=Men) | `W`, `M`       |
| `ad_name`         | string         | Human-readable ad name               | `Womens Ad A`  |
| `lifetime_spend`  | float          | Total spend across all weeks (ILS)   | `1245.32`      |
| `lifetime_leads`  | int            | Total leads across all weeks         | `28`           |
| `lifetime_cpl`    | float or empty | Lifetime cost per lead               | `44.48`        |
| `first_seen_week` | string         | ISO week of first spend              | `2025-W23`     |
| `last_seen_week`  | string         | ISO week of most recent spend        | `2026-W01`     |
| `weeks_active`    | int            | Number of distinct weeks with spend  | `15`           |

#### Notes

- Aggregates ALL weekly runs for each ad (not just last run)
- ~31 rows (one per ad in the system)
- Use for exploit vs. explore decisions (identify proven performers)

#### Example Row

```csv
campaign,ad_name,lifetime_spend,lifetime_leads,lifetime_cpl,first_seen_week,last_seen_week,weeks_active
W,Womens Ad A,1245.32,28,44.48,2025-W23,2026-W01,15
```

---

### 4. ad_components.csv

**Grain:** One row per ad

Maps each ad to its three creative components: media (image/video), headline, and text.

#### Columns

| Column          | Type            | Description                          | Example Values                   |
| --------------- | --------------- | ------------------------------------ | -------------------------------- |
| `ad_id`         | int             | Grist record ID for the ad           | `1`, `2`, `5`                    |
| `ad_name`       | string          | Human-readable ad name               | `Womens Ad B`                    |
| `campaign`      | string          | Campaign identifier (W=Women, M=Men) | `W`, `M`                         |
| `media_id`      | int or empty    | Grist record ID for media asset      | `14`, `5`                        |
| `media_name`    | string or empty | Name of media file                   | `Illustrated_Flow_Poster_Female` |
| `headline_id`   | int or empty    | Grist record ID for headline         | `14`                             |
| `headline_text` | string or empty | Actual headline text (Hebrew)        | `תנועה. עוצמה. חיוך.`            |
| `text_id`       | int or empty    | Grist record ID for ad text          | `12`                             |
| `text_name`     | string or empty | Name/variant of text                 | `Time Out For You`               |

#### Notes

- ~32 rows (one per ad in the system)
- Use for checking component reuse and ensuring no duplicate headlines/text within campaigns
- Empty values possible if component assignments are incomplete in Grist

#### Example Row

```csv
ad_id,ad_name,campaign,media_id,media_name,headline_id,headline_text,text_id,text_name
1,Womens Ad B,W,14,Illustrated_Flow_Poster_Female,14,"תנועה. עוצמה. חיוך.",12,Time Out For You
```

---

### 5. component_media_lifetime.csv

**Grain:** One row per media component

Lifetime aggregate performance metrics for each media asset across all ads that used it.

#### Columns

| Column          | Type           | Description                                  | Example Values                   |
| --------------- | -------------- | -------------------------------------------- | -------------------------------- |
| `media_id`      | int            | Grist record ID for the media asset          | `14`, `5`                        |
| `media_name`    | string         | Canonical media name                         | `Illustrated_Flow_Poster_Female` |
| `media_variant` | string or empty| Variant label for the media                  | `A`, `B`, empty                  |
| `media_format`  | string         | Media format                                 | `Image`, `Video`                 |
| `spend`         | float          | Total spend across all ads using this media  | `415.23`                         |
| `leads`         | int            | Total leads across all ads using this media  | `12`                             |
| `ads`           | int            | Number of distinct ads using this media      | `3`                              |
| `cpl`           | float or empty | Cost per lead (spend/leads), null if no leads| `34.60`, null                    |

#### Notes

- Aggregates ALL ad performance where this media appears
- Use for identifying proven or under-tested media assets

#### Example Row

```csv
media_id,media_name,media_variant,media_format,spend,leads,ads,cpl
14,Illustrated_Flow_Poster_Female,A,Image,415.23,12,3,34.60
```

---

### 6. component_headline_lifetime.csv

**Grain:** One row per headline component

Lifetime aggregate performance metrics for each headline across all ads that used it.

#### Columns

| Column          | Type           | Description                                   | Example Values            |
| --------------- | -------------- | --------------------------------------------- | ------------------------- |
| `headline_id`   | int            | Grist record ID for the headline              | `14`, `5`                 |
| `headline_text` | string         | Actual headline text                           | `תנועה. עוצמה. חיוך.`     |
| `spend`         | float          | Total spend across all ads using this headline| `512.10`                  |
| `leads`         | int            | Total leads across all ads using this headline| `14`                      |
| `ads`           | int            | Number of distinct ads using this headline    | `4`                       |
| `cpl`           | float or empty | Cost per lead (spend/leads), null if no leads | `36.58`, null             |

#### Notes

- Aggregates ALL ad performance where this headline appears
- Use for identifying historically strong or weak headline text

#### Example Row

```csv
headline_id,headline_text,spend,leads,ads,cpl
14,"תנועה. עוצמה. חיוך.",512.10,14,4,36.58
```

---

### 7. component_text_lifetime.csv

**Grain:** One row per text component

Lifetime aggregate performance metrics for each primary text across all ads that used it.

#### Columns

| Column         | Type           | Description                                   | Example Values          |
| -------------- | -------------- | --------------------------------------------- | ----------------------- |
| `text_id`      | int            | Grist record ID for the text                  | `12`, `5`               |
| `text_name`    | string         | Name/variant label for the text               | `Time Out For You`      |
| `text_variant` | string or empty| Variant label for the text                    | `A`, empty              |
| `primary_text` | string         | Full primary text content                      | (long text)             |
| `spend`        | float          | Total spend across all ads using this text    | `398.00`                |
| `leads`        | int            | Total leads across all ads using this text    | `9`                     |
| `ads`          | int            | Number of distinct ads using this text        | `3`                     |
| `cpl`          | float or empty | Cost per lead (spend/leads), null if no leads | `44.22`, null           |

#### Notes

- Aggregates ALL ad performance where this text appears
- Use for identifying strong or under-tested text variants

#### Example Row

```csv
text_id,text_name,text_variant,primary_text,spend,leads,ads,cpl
12,Time Out For You,A,"(full text omitted)",398.00,9,3,44.22
```

---

### 8. component_tags.csv

**Grain:** One row per component × tag assignment

Junction table mapping components (media, headline, text) to their taxonomic tags (style, energy, tone, promise, hook, structure).

#### Columns

| Column           | Type   | Description                   | Example Values                                                        |
| ---------------- | ------ | ----------------------------- | --------------------------------------------------------------------- |
| `component_type` | string | Type of component             | `media`, `headline`, `text`                                           |
| `component_id`   | int    | Grist record ID for component | `1`, `5`, `14`                                                        |
| `component_name` | string | Name or text of component     | `Shihonage_MF_Dojo_Photo`, `עוצמה, רוגע, ובטחון עצמי`                 |
| `tag_type`       | string | Taxonomy dimension            | `Media_Style`, `Media_Energy`, `Tone`, `Promise`, `Hook`, `Structure` |
| `tag_value`      | string | Specific tag value            | `Photo - Outside`, `Instructional / Demonstration`, `Promising`       |

#### Tag Types by Component

**Media components:**

- `Media_Style`: Style of visual (e.g., `Photo - Outside`, `Illustration - Poster`, `Photo - Dojo`)
- `Media_Energy`: Energy conveyed (e.g., `Dynamic / Throw`, `Meditative / Inspirational`)

**Headline components:**

- `Tone`: Emotional tone (e.g., `Promising`, `Empowering`, `Inviting`)
- `Promise`: Value proposition category (e.g., `Confidence`, `Peace`, `Strength`)
- `Hook`: Attention mechanism (e.g., `Question`, `Statement`, `Call to Action`)

**Text components:**

- `Hook`: Opening mechanism
- `Promise`: Value proposition category
- `Structure`: Format of the text (e.g., `Long`, `Short`)

#### Notes

- ~164 rows (components can have multiple tags)
- Use for ensuring tag diversity in weekly ad selection
- Use for analyzing performance by tag dimension (via joins with performance tables)

#### Example Rows

```csv
component_type,component_id,component_name,tag_type,tag_value
media,1,Shihonage_MF_Dojo_Photo,Media_Style,Illustration - Poster
media,1,Shihonage_MF_Dojo_Photo,Media_Energy,Instructional / Demonstration
headline,14,תנועה. עוצמה. חיוך.,Tone,Empowering
headline,14,תנועה. עוצמה. חיוך.,Promise,Strength
text,12,Time Out For You,Structure,Long
```
---

## Usage Notes for CSV

### Reading CSVs

Standard CSV format with:

- Comma delimiters
- Header row with column names
- UTF-8 encoding (important for Hebrew text)
- Empty cells for null/missing values

### Python Example

```python
import pandas as pd

# Read weekly performance
weekly = pd.read_csv('outputs/ad_weekly_performance.csv')

# Read component tags
tags = pd.read_csv('outputs/component_tags.csv')

# Join to analyze performance by media style
components = pd.read_csv('outputs/ad_components.csv')
media_tags = tags[tags['component_type'] == 'media']
performance_by_style = weekly.merge(components, on='ad_name').merge(
    media_tags, left_on='media_id', right_on='component_id'
)
```


---

### 9. performance_data.json

**Purpose:** Full Grist database export (raw JSON).

This file contains all tables and records from the ad tracking document, including derived tables and attachments metadata. It is the source used to generate the structured CSVs in this document.

### Usage notes

- Not intended for direct analysis; use the structured CSVs instead.
- Useful for audits or regenerating structured exports.


---

### 10. attachments_manifest.json

**Purpose:** Canonical registry of all media assets available for use in ads.

This file maps media identifiers to the actual files stored in `attachments.tar` and serves as the authoritative source for:

- media canonical names
- file paths inside the archive
- media type (image / video)
- descriptive metadata used for semantic checks

### Usage notes

- Any media referenced in ad planning **must appear in this manifest**.
- Media identity is determined by the canonical name in this file, not by filename heuristics.
- Agents must not invent or infer media outside this manifest.


---

## 11. attachments.tar

**Purpose:** Binary archive containing all media assets referenced in ads.

This archive contains the actual image and video files listed in `attachments_manifest.json`.

### Usage notes

- Media files must be accessed via their canonical names from `attachments_manifest.json`.
- Agents are expected to visually inspect media when required (e.g. image–text semantic checks).
- The archive is authoritative for determining actual media content, not filenames or tags alone.


---

## Data Freshness

Files are generated by:

```bash
pixi run export_ads
```

Workflow order:

1. Update `Weekly_runs` table in Grist with latest Facebook data
2. `pixi run transform_weekly` - Compute derived metrics
3. `pixi run export_ads` - Generate CSV files

Files reflect the state of Grist at export time. Re-run after updating source data.

---

## Changelog

- **2026-02-05**: Initial schema documentation
  - 5 tables: weekly performance, run summary, lifetime summary, components, component tags
  - CSV format as default (Parquet also supported via `--format parquet`)

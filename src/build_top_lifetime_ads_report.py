import argparse
import html
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_attachment_path(path_str: str) -> Path:
    return Path(path_str.replace("\\", "/"))


def pick_top_ads(data: dict, limit: int, campaign_filter: str) -> list[dict]:
    rows = []
    for record in data["tables"]["Derived_Lifetime_Ad_Metrics"]["records"]:
        fields = record.get("fields", {})
        leads = fields.get("Leads")
        cpl = fields.get("CPL")
        campaign_id = fields.get("Campaign")
        campaign = "W" if campaign_id == 1 else "M"

        if campaign_filter != "all" and campaign != campaign_filter:
            continue

        rows.append(
            {
                "campaign_id": campaign_id,
                "campaign": campaign,
                "ad_name": fields.get("Ad"),
                "lifetime_spend": float(fields.get("Spend") or 0),
                "lifetime_leads": int(leads or 0),
                "lifetime_cpl": None if cpl in (None, "") else float(cpl),
                "first_seen_week": fields.get("FirstWeek") or "",
                "last_seen_week": fields.get("LastWeek") or "",
                "weeks_active": int(fields.get("Weeks") or 0),
            }
        )

    rows.sort(
        key=lambda row: (
            -row["lifetime_leads"],
            float("inf") if row["lifetime_cpl"] is None else row["lifetime_cpl"],
            row["ad_name"] or "",
        )
    )
    return rows[:limit]


def build_attachment_index(manifest: dict, repo_root: Path) -> dict[str, dict]:
    index = {}
    for item in manifest.get("items", []):
        entry = dict(item)
        entry["absolute_path"] = repo_root / normalize_attachment_path(item["filepath"])
        index[str(item["attachment_id"])] = entry
    return index


def collect_lookup_tables(data: dict) -> dict[str, dict[int, dict]]:
    tables = {}
    for table_name in ["Ads", "Creatives", "Media", "Headlines", "Texts", "Campaigns"]:
        tables[table_name] = {
            record["id"]: record.get("fields", {})
            for record in data["tables"][table_name]["records"]
        }
    return tables


def safe_text(value: str | None) -> str:
    return html.escape(value or "")


def format_number(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{value:.2f}"


def copy_asset(src: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    shutil.copy2(src, dest)
    return dest


def build_ad_payloads(
    repo_root: Path,
    data: dict,
    manifest: dict,
    limit: int,
    campaign_filter: str,
    bundle_name: str,
    include_media: bool,
) -> tuple[list[dict], Path]:
    lookups = collect_lookup_tables(data)
    attachment_index = build_attachment_index(manifest, repo_root)
    ads_by_name = {
        fields.get("Name"): {"id": ad_id, **fields}
        for ad_id, fields in lookups["Ads"].items()
    }

    bundle_root = repo_root / "outputs" / bundle_name
    creative_dir = bundle_root / "assets" / "creatives"
    media_dir = bundle_root / "assets" / "media"

    payloads = []
    for rank, row in enumerate(
        pick_top_ads(data, limit, campaign_filter),
        start=1,
    ):
        ad = ads_by_name[row["ad_name"]]
        creative = lookups["Creatives"][ad["Creative"]]
        headline = lookups["Headlines"][creative["Headline"]]
        text = lookups["Texts"][ad["Text"]]

        creative_attachment = attachment_index[str(creative["Thumbnail"][1])]

        copied_creative = copy_asset(creative_attachment["absolute_path"], creative_dir)
        copied_media = None
        media = None

        if include_media:
            media = lookups["Media"][creative["Media"]]
            media_attachment = attachment_index[str(media["Media"][1])]
            copied_media = copy_asset(media_attachment["absolute_path"], media_dir)

        payloads.append(
            {
                "rank": rank,
                **row,
                "headline_text": headline.get("Text") or "",
                "primary_text": text.get("Primary_text") or "",
                "text_name": text.get("Name") or "",
                "text_variant": text.get("Variant") or "",
                "creative_name": creative.get("Name") or "",
                "canva_link": creative.get("Canva_link") or "",
                "media_name": "" if media is None else media.get("Name") or "",
                "media_variant": "" if media is None else media.get("Variant") or "",
                "creative_file": copied_creative.relative_to(bundle_root).as_posix(),
                "media_file": (
                    "" if copied_media is None else copied_media.relative_to(bundle_root).as_posix()
                ),
            }
        )

    return payloads, bundle_root


def render_html(payloads: list[dict], generated_at: str, title: str, include_media: bool) -> str:
    cards = []
    for item in payloads:
        text_label = item["text_name"]
        if item["text_variant"]:
            text_label = f"{text_label} ({item['text_variant']})"

        media_label = item["media_name"]
        if item["media_variant"]:
            media_label = f"{media_label} ({item['media_variant']})"

        image_block = f"""
  <div class="image-grid">
    <figure>
      <img src="{safe_text(item['creative_file'])}" alt="{safe_text(item['ad_name'])} creative preview" />
      <figcaption>Creative preview</figcaption>
    </figure>
  </div>
"""
        if include_media:
            image_block = f"""
  <div class="image-grid">
    <figure>
      <img src="{safe_text(item['creative_file'])}" alt="{safe_text(item['ad_name'])} creative preview" />
      <figcaption>Creative preview</figcaption>
    </figure>
    <figure>
      <img src="{safe_text(item['media_file'])}" alt="{safe_text(media_label)} media asset" />
      <figcaption>Underlying media: {safe_text(media_label)}</figcaption>
    </figure>
  </div>
"""

        cards.append(
            f"""
<section class="card">
  <div class="rank">#{item['rank']}</div>
  <h2>{safe_text(item['ad_name'])}</h2>
  <p class="meta">Campaign {safe_text(item['campaign'])} • {item['lifetime_leads']} lifetime leads • {format_number(item['lifetime_cpl'])} CPL • {format_number(item['lifetime_spend'])} ILS spend</p>
  <p class="meta">Seen {safe_text(item['first_seen_week'])} to {safe_text(item['last_seen_week'])} • {item['weeks_active']} active weeks</p>
  {image_block}
  <div class="copy-grid">
    <div>
      <h3>Headline</h3>
      <p class="headline">{safe_text(item['headline_text'])}</p>
    </div>
    <div>
      <h3>Primary Text</h3>
      <pre>{safe_text(item['primary_text'])}</pre>
    </div>
  </div>
  <p class="meta">Text asset: {safe_text(text_label)}</p>
  {f'<p class="meta"><a href="{html.escape(item["canva_link"], quote=True)}">Canva link</a></p>' if item["canva_link"] else ""}
</section>
"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{safe_text(title)}</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --paper: #fffdf8;
      --ink: #1e1b16;
      --muted: #6d655a;
      --line: #d7cbbb;
      --accent: #a54a2a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(165, 74, 42, 0.08), transparent 30%),
        linear-gradient(180deg, #f8f4eb 0%, var(--bg) 100%);
      color: var(--ink);
      font: 16px/1.55 Georgia, "Times New Roman", serif;
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 40px 20px 64px;
    }}
    h1 {{
      font-size: 2.6rem;
      margin: 0 0 10px;
      letter-spacing: -0.02em;
    }}
    .intro {{
      color: var(--muted);
      margin: 0 0 28px;
    }}
    .card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 24px;
      margin: 0 0 24px;
      box-shadow: 0 18px 40px rgba(30, 27, 22, 0.05);
    }}
    .rank {{
      color: var(--accent);
      font-weight: 700;
      font-size: 0.95rem;
      margin-bottom: 6px;
    }}
    h2 {{
      margin: 0 0 8px;
      font-size: 2rem;
    }}
    h3 {{
      margin: 0 0 10px;
      font-size: 1.1rem;
    }}
    .meta {{
      color: var(--muted);
      margin: 0 0 10px;
    }}
    .image-grid, .copy-grid {{
      display: grid;
      gap: 20px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      margin: 18px 0;
    }}
    figure {{
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 16px;
      overflow: hidden;
      background: #fff;
    }}
    img {{
      width: 100%;
      display: block;
      background: #eee;
    }}
    figcaption {{
      padding: 10px 14px;
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .headline {{
      font-size: 1.25rem;
      margin: 0;
    }}
    pre {{
      margin: 0;
      white-space: pre-wrap;
      font: inherit;
      background: #fbf8f1;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
    }}
    a {{
      color: var(--accent);
    }}
    @media (max-width: 800px) {{
      .image-grid, .copy-grid {{
        grid-template-columns: 1fr;
      }}
      h1 {{
        font-size: 2rem;
      }}
      h2 {{
        font-size: 1.5rem;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <h1>{safe_text(title)}</h1>
    <p class="intro">Generated {safe_text(generated_at)} from the live Grist ad-tracking document. Ranked by lifetime leads descending, with lifetime CPL used as the tie-breaker.</p>
    {''.join(cards)}
  </main>
</body>
</html>
"""


def render_markdown(
    payloads: list[dict],
    generated_at: str,
    title: str,
    include_media: bool,
) -> str:
    sections = [
        f"# {title}",
        "",
        f"Generated {generated_at} from the live Grist ad-tracking document.",
        "",
        "Ranking method: lifetime leads descending, with lifetime CPL as the tie-breaker.",
        "",
    ]

    for item in payloads:
        text_label = item["text_name"]
        if item["text_variant"]:
            text_label = f"{text_label} ({item['text_variant']})"

        media_label = item["media_name"]
        if item["media_variant"]:
            media_label = f"{media_label} ({item['media_variant']})"

        item_lines = [
            f"## #{item['rank']} {item['ad_name']}",
            "",
            f"- Campaign: {item['campaign']}",
            f"- Lifetime leads: {item['lifetime_leads']}",
            f"- Lifetime CPL: {format_number(item['lifetime_cpl'])}",
            f"- Lifetime spend: {format_number(item['lifetime_spend'])} ILS",
            f"- First seen week: {item['first_seen_week']}",
            f"- Last seen week: {item['last_seen_week']}",
            f"- Weeks active: {item['weeks_active']}",
            f"- Creative preview: `{item['creative_file']}`",
        ]
        if include_media:
            item_lines.append(f"- Media asset: `{item['media_file']}` ({media_label})")
        item_lines.extend(
            [
                f"- Text asset: {text_label}",
                "",
                f"### Headline\n{item['headline_text']}",
                "",
                "### Primary Text",
                item["primary_text"],
                "",
            ]
        )
        sections.extend(item_lines)
        if item["canva_link"]:
            sections.extend([f"- Canva link: {item['canva_link']}", ""])

    return "\n".join(sections)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a top lifetime ads report.")
    parser.add_argument("--limit", type=int, default=5, help="Number of ads to include.")
    parser.add_argument(
        "--campaign",
        choices=["all", "W", "M"],
        default="all",
        help="Optional campaign filter.",
    )
    parser.add_argument(
        "--bundle-name",
        default="top_5_lifetime_ads_bundle",
        help="Output folder name under outputs/.",
    )
    parser.add_argument(
        "--title",
        default="Top 5 Lifetime-Performing Ads",
        help="Report title.",
    )
    parser.add_argument(
        "--creative-only",
        action="store_true",
        help="Skip underlying media assets and only include the creative preview plus text.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    outputs_dir = repo_root / "outputs"
    bundle_root = outputs_dir / args.bundle_name

    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    bundle_root.mkdir(parents=True, exist_ok=True)

    data = load_json(outputs_dir / "performance_data.json")
    manifest = load_json(outputs_dir / "attachments_manifest.json")
    payloads, bundle_root = build_ad_payloads(
        repo_root=repo_root,
        data=data,
        manifest=manifest,
        limit=args.limit,
        campaign_filter=args.campaign,
        bundle_name=args.bundle_name,
        include_media=not args.creative_only,
    )
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html_output = bundle_root / "top_5_lifetime_ads_report.html"
    md_output = bundle_root / "top_5_lifetime_ads_report.md"
    json_output = bundle_root / "top_5_lifetime_ads_report.json"

    html_output.write_text(
        render_html(
            payloads,
            generated_at,
            args.title,
            include_media=not args.creative_only,
        ),
        encoding="utf-8",
    )
    md_output.write_text(
        render_markdown(
            payloads,
            generated_at,
            args.title,
            include_media=not args.creative_only,
        ),
        encoding="utf-8",
    )
    json_output.write_text(
        json.dumps(payloads, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Built report bundle at {bundle_root}")


if __name__ == "__main__":
    main()

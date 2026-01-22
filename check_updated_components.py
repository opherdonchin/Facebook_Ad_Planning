#!/usr/bin/env python3
"""Check the updated component tables with new columns."""

from src.grist import GristClient
import json

c = GristClient("c5dzrhUn5QHF", "eaa7ac30d29bd1a81816e6c5cf365b31428ee574")

print("=" * 80)
print("MEDIA COMPONENTS (Top 5)")
print("=" * 80)
media = c.fetch_records("Derived_Component_Media_Lifetime", flat=True)
for i, row in enumerate(media[:5], 1):
    print(f"\n{i}. {row.get('Name', row.get('Media_Name', 'N/A'))}")
    print(f"   CPL: {row.get('CPL', 'N/A'):.2f}")
    print(f"   Spend: {row['Spend']:.2f}, Leads: {row['Leads']}, Ads: {row['Ads']}")
    print(
        f"   Variant: {row.get('Variant', 'N/A')}, Format: {row.get('Format', 'N/A')}"
    )
    if "Media" in row:
        print(f"   Media: {row['Media']}")

print("\n" + "=" * 80)
print("HEADLINE COMPONENTS (Top 5)")
print("=" * 80)
headlines = c.fetch_records("Derived_Component_Headline_Lifetime", flat=True)
for i, row in enumerate(headlines[:5], 1):
    print(f"\n{i}. Headline ID {row['Headline_ID']}")
    print(f"   Text: {row.get('Text', 'N/A')}")
    print(
        f"   CPL: {row.get('CPL', 'N/A'):.2f}, Spend: {row['Spend']:.2f}, Leads: {row['Leads']}, Ads: {row['Ads']}"
    )

print("\n" + "=" * 80)
print("TEXT COMPONENTS (Top 5)")
print("=" * 80)
texts = c.fetch_records("Derived_Component_Text_Lifetime", flat=True)
for i, row in enumerate(texts[:5], 1):
    print(f"\n{i}. Text ID {row['Text_ID']}")
    print(f"   Name: {row.get('Name', 'N/A')}, Variant: {row.get('Variant', 'N/A')}")
    print(
        f"   CPL: {row.get('CPL', 'N/A'):.2f}, Spend: {row['Spend']:.2f}, Leads: {row['Leads']}, Ads: {row['Ads']}"
    )
    text = row.get("Primary_text", "")
    if text:
        preview = text[:100] + "..." if len(text) > 100 else text
        print(f"   Text: {preview}")

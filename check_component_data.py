#!/usr/bin/env python3
"""Quick script to check component metric tables."""

from src.grist import GristClient
import json

# Initialize client
c = GristClient("c5dzrhUn5QHF", "eaa7ac30d29bd1a81816e6c5cf365b31428ee574")

print("=" * 80)
print("MEDIA COMPONENTS (Top 10 by CPL)")
print("=" * 80)
media = c.fetch_records("Derived_Component_Media_Lifetime", flat=True)
for i, row in enumerate(media[:10], 1):
    print(
        f"{i}. {row['Media_Name']:<40} CPL: {row.get('CPL', 'N/A'):>8.2f}  Spend: {row['Spend']:>8.2f}  Leads: {row['Leads']:>3}"
    )

print("\n" + "=" * 80)
print("HEADLINE COMPONENTS (Top 10 by CPL)")
print("=" * 80)
headlines = c.fetch_records("Derived_Component_Headline_Lifetime", flat=True)
for i, row in enumerate(headlines[:10], 1):
    print(
        f"{i}. Headline ID {row['Headline_ID']:<3}  CPL: {row.get('CPL', 'N/A'):>8.2f}  Spend: {row['Spend']:>8.2f}  Leads: {row['Leads']:>3}  Ads: {row['Ads']}"
    )

print("\n" + "=" * 80)
print("TEXT COMPONENTS (Top 10 by CPL)")
print("=" * 80)
texts = c.fetch_records("Derived_Component_Text_Lifetime", flat=True)
for i, row in enumerate(texts[:10], 1):
    print(
        f"{i}. Text ID {row['Text_ID']:<3}  CPL: {row.get('CPL', 'N/A'):>8.2f}  Spend: {row['Spend']:>8.2f}  Leads: {row['Leads']:>3}  Ads: {row['Ads']}"
    )

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total Media components: {len(media)}")
print(f"Total Headline components: {len(headlines)}")
print(f"Total Text components: {len(texts)}")

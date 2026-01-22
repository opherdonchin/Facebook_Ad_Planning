#!/usr/bin/env python3
"""Verify component metrics match ad-level aggregations."""

from src.grist import GristClient

c = GristClient("c5dzrhUn5QHF", "eaa7ac30d29bd1a81816e6c5cf365b31428ee574")

# Get lifetime ad metrics
ads = c.fetch_records("Derived_Lifetime_Ad_Metrics", flat=True)

# Check Mens Ad A which should use "Shihonage_MF_Dojo_Photo"
mens_ad_a = [a for a in ads if a.get("Ad") == "Mens Ad A"]
if mens_ad_a:
    ad = mens_ad_a[0]
    print(f"Mens Ad A:")
    print(f"  CPL: {ad.get('CPL', 'N/A')}")
    print(f"  Spend: {ad['Spend']}")
    print(f"  Leads: {ad['Leads']}")
    print()

# Let's verify the media aggregation manually
# Get all ads and their creative -> media mappings
creatives = c.fetch_records("Creatives", flat=True)
media_table = c.fetch_records("Media", flat=True)
ads_table = c.fetch_records("Ads", flat=True)

# Build media ID -> name mapping
media_map = {m["id"]: m.get("Name", "Unknown") for m in media_table}

# Build creative ID -> media name mapping
creative_to_media = {}
for cr in creatives:
    media_id = cr.get("Media")
    if isinstance(media_id, list) and len(media_id) > 0:
        media_id = media_id[0]
    creative_to_media[cr["id"]] = media_map.get(media_id, "Unknown")

# Build ad -> media mapping
ad_to_media = {}
for ad in ads_table:
    creative_id = ad.get("Creative")
    if isinstance(creative_id, list) and len(creative_id) > 0:
        creative_id = creative_id[0]
    ad_name = ad.get("Name", "Unknown")
    ad_to_media[ad_name] = creative_to_media.get(creative_id, "Unknown")

# Verify "Shihonage_MF_Dojo_Photo"
media_name = "Shihonage_MF_Dojo_Photo"
ads_using_media = [ad_name for ad_name, m in ad_to_media.items() if m == media_name]

print(f"Ads using '{media_name}':")
total_spend = 0
total_leads = 0
for ad_name in ads_using_media:
    ad_data = [a for a in ads if a.get("Ad") == ad_name]
    if ad_data:
        ad = ad_data[0]
        spend = ad["Spend"]
        leads = ad["Leads"]
        cpl = ad.get("CPL", "N/A")
        total_spend += spend
        total_leads += leads
        print(f"  - {ad_name}: Spend={spend:.2f}, Leads={leads}, CPL={cpl}")

print(f"\nAggregated for media '{media_name}':")
print(f"  Total Spend: {total_spend:.2f}")
print(f"  Total Leads: {total_leads}")
print(
    f"  Calculated CPL: {total_spend / total_leads if total_leads > 0 else 'N/A':.2f}"
)

print("\nExpected from component table: CPL=39.26, Spend=824.41, Leads=21")

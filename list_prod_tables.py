from src.utils import load_config
from src.grist.grist import GristClient

config = load_config("config.json")
# Use ad_tracking profile
profile = config.get("ad_tracking")
client = GristClient(profile["doc_id"], profile["api_key"], profile["server"])

print(f"Listing tables for doc: {profile['doc_id']}")
tables = client.get_tables()
found = False
for t in tables:
    print(f" - {t['id']}")
    if t["id"] == "Ads":
        found = True

if found:
    print("\nColumns for Ads:")
    cols = client.get_table_columns("Ads")
    print([c["id"] for c in cols])

print("\nColumns for Weekly_runs:")
try:
    cols = client.get_table_columns("Weekly_runs")
    print([c["id"] for c in cols])
except:
    print("Could not get columns for Weekly_runs")

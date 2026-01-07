from src.utils import load_config
from src.grist.grist import GristClient

config = load_config("config.json")
# Use ad_tracking profile
profile = config.get("ad_tracking")
client = GristClient(profile["doc_id"], profile["api_key"], profile["server"])

records = client.fetch_records("Weekly_runs", flat=True)
if records:
    print(records[0])

    # Try to find Campaign info. In Grist, reference columns often come down as IDs.
    # But flattening often brings them down differently.
    # Also 'Ad' might be a reference to the 'Ads' table, which has 'Campaign'.

    # Let's check if 'Ad' is an integer (reference)
    ad_val = records[0].get("Ad")
    print(f"Ad value: {ad_val} (type: {type(ad_val)})")
else:
    print("No records found in Weekly_runs")

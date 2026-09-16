import argparse

import requests

from src.utils import load_config, require_grist_profile

parser = argparse.ArgumentParser(description="List tables for a configured Grist profile.")
parser.add_argument("--profile", default="ad_tracking")
args = parser.parse_args()

config = load_config("config.json")
profile = require_grist_profile(config, args.profile)
doc_id = profile["doc_id"]
api_key = profile["api_key"]
server = profile["server"]

print(f"Doc ID: {doc_id}")
print(f"Server: {server}")

headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

url = f"{server}/api/docs/{doc_id}/tables"
print(f"Listing tables from {url}")
r = requests.get(url, headers=headers)
try:
    r.raise_for_status()
    tables = r.json()
    print("Tables found:")
    for t in tables.get("tables", []):
        print(f" - {t['id']}")
except Exception as e:
    print(r.text)
    raise e

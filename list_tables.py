from src.utils import load_config
from src.grist.grist import GristClient
import requests

config = load_config("config.json")
test_config = config.get("test", {})
doc_id = test_config.get("doc_id")
api_key = test_config.get("api_key") or config.get("ad_tracking", {}).get("api_key")
server = test_config.get("server", "https://docs.getgrist.com")

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

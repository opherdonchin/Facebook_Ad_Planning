from src.grist.grist import GristClient
import json
from datetime import datetime

cfg = json.load(open('config.json'))
ad_cfg = cfg['ad_tracking']
client = GristClient(ad_cfg['doc_id'], ad_cfg['api_key'])
records = client.fetch_records('Weekly_runs', flat=True)

print('Last 6 records:')
for r in records[-6:]:
    dt = datetime.fromtimestamp(r['Week']) if r['Week'] else None
    print(f"  ID {r['id']}: Week={dt.date() if dt else 'None'}, Ad={r['Ad']}, Spend={r['Spend']}, Leads={r['Leads']}, A={r['A']}")

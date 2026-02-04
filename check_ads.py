from src.grist.grist import GristClient
import json

cfg = json.load(open('config.json'))
ad_cfg = cfg['ad_tracking']
client = GristClient(ad_cfg['doc_id'], ad_cfg['api_key'])
ads = client.fetch_records('Ads', flat=True)

print('Ad ID -> Name mapping for IDs 24, 26, 29, 30, 31, 32:')
for ad in ads:
    ad_id = ad.get('id')
    name = ad.get('Name')
    if ad_id in [24, 26, 29, 30, 31, 32]:
        print(f'  {ad_id}: {name}')

print('\nAll ads in table:')
for ad in sorted(ads, key=lambda x: x.get('id', 0)):
    print(f'  {ad.get("id")}: {ad.get("Name")}')

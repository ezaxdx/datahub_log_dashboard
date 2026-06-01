# -*- coding: utf-8 -*-
import sys, os, tomllib, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config, data

secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
with open(secrets_path, 'rb') as f:
    secrets = tomllib.load(f)
TOKEN = secrets.get('api', {}).get('token', '')
HEADERS = {'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'}
resp = requests.get(config.API_BASE_URL + config.API_ENDPOINT_USERS, headers=HEADERS, verify=False, timeout=30)
records = resp.json()
if isinstance(records, dict):
    records = records.get('data', {}).get('list', records.get('list', []))

df = data._build_users_df(records)

for rank in ['선임연구원', '책임연구원']:
    sub = df[df['_eff_rankNm'] == rank]
    print(f'=== {rank}: {len(sub)}명 ===')
    for _, r in sub.iterrows():
        status = r['재직상태']
        name   = r['임직원명']
        dept   = r['_eff_deptNm']
        hq     = r['_eff_hqNm']
        print(f'  [{status}] {name}  ({dept} / {hq})')
    print()

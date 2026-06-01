# -*- coding: utf-8 -*-
import sys, os, tomllib, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
with open(secrets_path, 'rb') as f:
    secrets = tomllib.load(f)
TOKEN = secrets.get('api', {}).get('token', '')
HEADERS = {'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'}
resp = requests.get(config.API_BASE_URL + config.API_ENDPOINT_USERS, headers=HEADERS, verify=False, timeout=30)
records = resp.json()
if isinstance(records, dict):
    records = records.get('data', {}).get('list', records.get('list', []))

for r in records:
    name = r.get('userNm', '')
    if '황보' in name or '정운' in name:
        uno    = str(r.get('userNo', '')).zfill(3)
        retire = r.get('retireDt') or ''
        hire   = r.get('hireDt') or ''
        h2026  = next((h for h in r.get('history', []) if str(h.get('year', '')) == '2026'), {})
        print(f"UserNo={uno}  name={name!r}")
        print(f"  hireDt={hire!r}  retireDt={retire!r}")
        print(f"  2026: dept={h2026.get('deptNm')!r}  hq={h2026.get('hqNm')!r}  div={h2026.get('divisionNm')!r}  rank={h2026.get('statPositionNm')!r}")
        print()

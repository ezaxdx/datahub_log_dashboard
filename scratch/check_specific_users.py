# -*- coding: utf-8 -*-
"""특정 유저 raw API 데이터 확인"""
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

TARGET_UNOS = {'387', '416', '500', '515'}

for r in records:
    uno = str(r.get('userNo', '')).zfill(3)
    if uno not in TARGET_UNOS:
        continue
    print(f'UserNo={uno}  name={r.get("userNm")!r}  prsId={r.get("prsId")!r}')
    print(f'  hireDt={r.get("hireDt")!r}  retireDt={r.get("retireDt")!r}')
    history = r.get('history', [])
    if history:
        for h in history:
            print(f'  [{h.get("year")}] dept={h.get("deptNm")!r}  hq={h.get("hqNm")!r}  div={h.get("divisionNm")!r}  rank={h.get("statPositionNm")!r}')
    else:
        print('  history: (없음)')
    print()

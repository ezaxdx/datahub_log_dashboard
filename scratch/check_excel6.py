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

print('=== 엑셀/excel 포함 계정 ===')
found = 0
for r in records:
    name = r.get('userNm', '') or ''
    prsid = r.get('prsId', '') or ''
    uno = str(r.get('userNo', '')).zfill(3)
    if '엑셀' in name or 'excel' in prsid.lower() or 'excel' in name.lower():
        found += 1
        retire = r.get('retireDt') or ''
        h = next((hh for hh in r.get('history', []) if str(hh.get('year',''))=='2026'), {})
        print(f'UserNo={uno}  name={name!r}  prsId={prsid!r}  retireDt={retire!r}')
        print(f'  dept={h.get("deptNm")!r}  hq={h.get("hqNm")!r}  rank={h.get("statPositionNm")!r}')

if not found:
    print('(없음)')

# 혹시 prsId에 숫자6 포함하는 계정도 확인
print('\n=== 전체 계정 중 이름에 숫자 포함 테스트성 계정 ===')
for r in records:
    name = r.get('userNm', '') or ''
    prsid = r.get('prsId', '') or ''
    uno = str(r.get('userNo', '')).zfill(3)
    # 이름이 짧고 숫자 포함하는 계정
    if any(c.isdigit() for c in name) and len(name) <= 6:
        retire = r.get('retireDt') or ''
        h = next((hh for hh in r.get('history', []) if str(hh.get('year',''))=='2026'), {})
        print(f'UserNo={uno}  name={name!r}  prsId={prsid!r}  retireDt={retire!r}  dept={h.get("deptNm")!r}')

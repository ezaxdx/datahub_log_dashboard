# -*- coding: utf-8 -*-
"""
ICT융합개발본부/MICE혁신본부 _ui_dept 구조 전체 확인
→ DEFAULT_EXCLUDE_DEPTS에 어떤 값이 들어가야 하는지 파악
"""
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

YEAR = str(config.CURRENT_YEAR)
TEST_UNOS  = set(str(u).zfill(3) for u in config.TEST_ACCOUNT_USERNOS)
EXEC_RANKS = {'임원', '총괄대표', '대표이사'}

rows = []
for r in records:
    if r.get('retireDt'):
        continue
    uno  = str(r.get('userNo', '')).zfill(3)
    name = r.get('userNm', '')
    h = next((hh for hh in r.get('history', []) if str(hh.get('year', '')) == YEAR), {})
    dept = (h.get('deptNm') or '').strip()
    hq   = (h.get('hqNm') or '').strip()
    div  = (h.get('divisionNm') or '').strip()
    rank = (h.get('statPositionNm') or '').strip()

    if uno in TEST_UNOS:
        ui = 'Test'
    elif rank in EXEC_RANKS:
        ui = 'M-Level'
    else:
        ui = dept or hq or div or 'M-Level'

    rows.append({'name': name, 'uno': uno, 'dept': dept, 'hq': hq, 'div': div, 'rank': rank, 'ui': ui})

TARGET_DIVS = {'디지털융합혁신부'}
TARGET_HQS  = {'ICT융합개발본부', 'MICE혁신본부'}

print('=== 디지털융합혁신부(ICT계열) 전체 _ui_dept 구조 ===')
print(f'  {"UserNo":6s}  {"이름":8s}  {"_ui_dept":20s}  {"dept":20s}  {"hq":20s}  {"rank"}')
print('  ' + '-'*90)
for r in sorted([x for x in rows if x['div'] in TARGET_DIVS or x['hq'] in TARGET_HQS],
                key=lambda x: (x['div'], x['hq'], x['dept'], x['name'])):
    print(f'  {r["uno"]:6s}  {r["name"]:8s}  {r["ui"]:20s}  {r["dept"]:20s}  {r["hq"]:20s}  {r["rank"]}')

print()
print('=== 현재 DEFAULT_EXCLUDE_DEPTS ===')
for d in config.DEFAULT_EXCLUDE_DEPTS:
    print(f'  {d!r}')

print()
print('=== _ui_dept 기준: ICT/MICE 관련 항목 중 현재 제외되지 않는 것 ===')
excluded = set(config.DEFAULT_EXCLUDE_DEPTS)
for r in sorted([x for x in rows if x['div'] in TARGET_DIVS or x['hq'] in TARGET_HQS],
                key=lambda x: x['ui']):
    if r['ui'] not in excluded:
        print(f'  ⚠  {r["uno"]:6s}  {r["name"]:8s}  _ui_dept={r["ui"]!r}  (div={r["div"]}, hq={r["hq"]})')

# -*- coding: utf-8 -*-
"""
M-Level 현황 + ICT융합개발본부 전체 인원 확인
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
NULL_VALS  = {'nan', 'NaN', 'None', ''}
SHOW_AS_HQ   = set(config.DEPT_SHOW_AS_HQ)
SHOW_AS_TEAM = set(config.DEPT_SHOW_AS_TEAM)

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

    # _ui_dept (현재 사이드바 기준)
    if uno in TEST_UNOS:
        ui = '테스트 계정'
    elif rank in EXEC_RANKS:
        ui = 'M-Level'
    else:
        ui = dept or hq or div or 'M-Level'

    rows.append({'name': name, 'uno': uno, 'dept': dept, 'hq': hq, 'div': div, 'rank': rank, 'ui': ui})

# ── M-Level 현황 ──
print(f'=== M-Level 현황 ({sum(1 for r in rows if r["ui"]=="M-Level")}명) ===')
print(f'  {"이름":8s}  {"dept":20s}  {"hq":20s}  {"div":22s}  {"rank"}')
print('  ' + '-'*85)
for r in sorted([r for r in rows if r['ui'] == 'M-Level'], key=lambda x: (x['rank'], x['name'])):
    print(f'  {r["name"]:8s}  {r["dept"]:20s}  {r["hq"]:20s}  {r["div"]:22s}  {r["rank"]}')

# ── ICT융합개발본부 전체 ──
print()
ict_rows = [r for r in rows if r['hq'] == 'ICT융합개발본부']
print(f'=== ICT융합개발본부 전체 ({len(ict_rows)}명) ===')
print(f'  {"이름":8s}  {"dept":20s}  {"rank"}')
print('  ' + '-'*45)
for r in sorted(ict_rows, key=lambda x: (x['dept'], x['name'])):
    print(f'  {r["name"]:8s}  {r["dept"]:20s}  {r["rank"]}')

# -*- coding: utf-8 -*-
"""M-Level 비임원 인원 상세 + UserNo 확인"""
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

PROBLEM_NAMES = {'연구소 구성원 테스트', '조수아', '김미선', '강민구', '구성원1', '조민경', 'pm1'}

print('=== M-Level 비임원 상세 (UserNo 포함) ===')
print(f'  {"UserNo":6s}  {"이름":14s}  {"prsId":35s}  {"dept":15s}  {"hq":15s}  {"div":20s}  {"rank":10s}  {"입사일"}')
print('  ' + '-'*120)

for r in records:
    name = r.get('userNm', '')
    if name not in PROBLEM_NAMES:
        continue
    uno   = str(r.get('userNo', '')).zfill(3)
    prsid = str(r.get('prsId', '') or '').strip()
    hire  = str(r.get('hireDt', '') or '').strip()
    retire = str(r.get('retireDt', '') or '').strip()
    h = next((hh for hh in r.get('history', []) if str(hh.get('year', '')) == YEAR), {})
    dept = (h.get('deptNm') or '').strip()
    hq   = (h.get('hqNm') or '').strip()
    div  = (h.get('divisionNm') or '').strip()
    rank = (h.get('statPositionNm') or '').strip()

    retired_tag = ' [퇴사]' if retire else ''
    in_test = ' ← 테스트계정' if uno in TEST_UNOS else ''
    print(f'  {uno:6s}  {name:14s}  {prsid:35s}  {dept:15s}  {hq:15s}  {div:20s}  {rank:10s}  {hire}{retired_tag}{in_test}')

print()
print('=== 현재 TEST_ACCOUNT_USERNOS ===')
for u in config.TEST_ACCOUNT_USERNOS:
    print(f'  {str(u).zfill(3)}')

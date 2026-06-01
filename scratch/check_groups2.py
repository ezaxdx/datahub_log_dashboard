# -*- coding: utf-8 -*-
"""
_ui_dept 항목 중 이상한 값들이 부서_그룹 기준으로 어디에 속하는지 확인
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
    h = next((h for h in r.get('history', []) if str(h.get('year', '')) == YEAR), {})
    dept = (h.get('deptNm') or '').strip()
    hq   = (h.get('hqNm') or '').strip()
    div  = (h.get('divisionNm') or '').strip()
    rank = (h.get('statPositionNm') or '').strip()

    # _ui_dept
    if uno in TEST_UNOS:
        ui = '테스트 계정'
    elif rank in EXEC_RANKS:
        ui = 'M-Level'
    else:
        ui = dept or hq or div or 'M-Level'

    # 부서_그룹
    if uno in TEST_UNOS:
        grp = '테스트 계정'
    elif rank in EXEC_RANKS:
        grp = 'M-Level'
    elif dept in SHOW_AS_TEAM:
        grp = dept
    elif hq in SHOW_AS_HQ:
        grp = hq
    elif div and div not in NULL_VALS:
        grp = div
    elif hq:
        grp = hq
    else:
        grp = 'M-Level'

    rows.append({'name': name, 'uno': uno, 'dept': dept, 'hq': hq, 'div': div, 'rank': rank, 'ui': ui, 'grp': grp})

# 디키디키 확인
print('=== 디키디키 팀 상세 ===')
for r in rows:
    if r['ui'] == '디키디키':
        print(f"  {r['name']:8s} | dept={r['dept']:20s} | hq={r['hq']:20s} | div={r['div']:20s} | rank={r['rank']:10s} | 부서_그룹={r['grp']}")

print()
# AXDX팀 / ICT 확인
print('=== AXDX팀 / ICT융합개발본부 → 부서_그룹 ===')
for r in rows:
    if r['div'] in ('디지털융합혁신부', '') or r['hq'] in ('ICT융합개발본부',) or r['dept'] in ('AXDX팀',):
        if 'AXDX' in r['dept'] or 'ICT' in r['hq'] or r['div'] == '디지털융합혁신부':
            print(f"  {r['name']:8s} | dept={r['dept']:20s} | hq={r['hq']:20s} | div={r['div']:20s} | rank={r['rank']:10s} | 부서_그룹={r['grp']}")

print()
# 본부장급 1인 항목 확인 (_ui_dept에만 나오는 이상한 값들)
weird_uis = ['E&E 1본부', '컨벤션 1본부', '컨벤션 2본부', '스마트립사업 본부',
             '비즈니스커넥트사업본부', '경영관리본부', '글로컬관광CX실', '글로컬CX팀']
print(f'=== 본부장급 항목 → 부서_그룹 확인 ===')
for r in rows:
    if r['ui'] in weird_uis:
        print(f"  {r['name']:8s} | dept={r['dept']:20s} | hq={r['hq']:20s} | div={r['div']:20s} | rank={r['rank']:10s} | 부서_그룹={r['grp']}")

print()
# DEFAULT_EXCLUDE_DEPTS가 부서_그룹 기준으로 어떻게 대응되는지 확인
print(f'=== 제외 대상 부서_그룹 목록 확인 ===')
from collections import Counter
grp_by_ui_source = {}   # 부서_그룹 → {_ui_dept 원본들}
for r in rows:
    grp_by_ui_source.setdefault(r['grp'], set()).add(r['ui'])

for excl in config.DEFAULT_EXCLUDE_DEPTS:
    found = [g for g, uis in grp_by_ui_source.items() if excl in uis or excl == g]
    print(f"  config 제외: {excl:20s}  →  부서_그룹: {found}")

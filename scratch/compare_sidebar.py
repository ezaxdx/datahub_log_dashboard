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

YEAR = str(config.CURRENT_YEAR)
TEST_UNOS  = set(str(u).zfill(3) for u in config.TEST_ACCOUNT_USERNOS)
EXEC_RANKS = {'임원', '총괄대표', '대표이사'}
NULL_VALS  = {'nan', 'NaN', 'None', ''}
SHOW_AS_HQ   = set(config.DEPT_SHOW_AS_HQ)
SHOW_AS_TEAM = set(config.DEPT_SHOW_AS_TEAM)

ui_depts = {}
groups   = {}

for r in records:
    if r.get('retireDt'):
        continue
    uno = str(r.get('userNo', '')).zfill(3)
    h = next((h for h in r.get('history', []) if str(h.get('year', '')) == YEAR), {})
    dept = (h.get('deptNm') or '').strip()
    hq   = (h.get('hqNm') or '').strip()
    div  = (h.get('divisionNm') or '').strip()
    rank = (h.get('statPositionNm') or '').strip()

    # _ui_dept 계산
    if uno in TEST_UNOS:
        ui = '테스트 계정'
    elif rank in EXEC_RANKS:
        ui = 'M-Level'
    else:
        ui = dept or hq or div or 'M-Level'

    # 부서_그룹 계산
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

    ui_depts[ui]  = ui_depts.get(ui, 0)  + 1
    groups[grp]   = groups.get(grp, 0)   + 1

print(f"=== _ui_dept (팀 단위) — {len(ui_depts)}개 항목 ===")
for k, v in sorted(ui_depts.items(), key=lambda x: -x[1]):
    print(f"  {v:3d}명  {k}")

print()
print(f"=== 부서_그룹 (본부/사업부 단위) — {len(groups)}개 항목 ===")
for k, v in sorted(groups.items(), key=lambda x: -x[1]):
    print(f"  {v:3d}명  {k}")

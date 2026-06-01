# -*- coding: utf-8 -*-
"""
3_department.py '부서/직급별 인원 현황' 피벗 테이블 검증
- 비표준 직급 인원이 누락되는지 확인
- 사업부별 합계가 실제 인원과 맞는지 확인
"""
import sys, os, tomllib, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import pandas as pd
from datetime import date as _date

secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
with open(secrets_path, 'rb') as f:
    secrets = tomllib.load(f)
TOKEN = secrets.get('api', {}).get('token', '')
HEADERS = {'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'}
resp = requests.get(config.API_BASE_URL + config.API_ENDPOINT_USERS, headers=HEADERS, verify=False, timeout=30)
records = resp.json()
if isinstance(records, dict):
    records = records.get('data', {}).get('list', records.get('list', []))

YEAR       = str(config.CURRENT_YEAR)
TEST_UNOS  = set(str(u).zfill(3) for u in config.TEST_ACCOUNT_USERNOS)
EXEC_RANKS = {'임원', '총괄대표', '대표이사'}
SHOW_AS_HQ   = set(config.DEPT_SHOW_AS_HQ)
SHOW_AS_TEAM = set(config.DEPT_SHOW_AS_TEAM)
TODAY      = _date.today().isoformat()
exclude_groups = {"M-Level", "㈜이즈피엠피", "Test"}

rows = []
for r in records:
    uno    = str(r.get('userNo', '')).zfill(3)
    name   = r.get('userNm', '')
    retire = r.get('retireDt') or ''
    # 날짜 비교 (오늘 이후 퇴사 예정자는 재직)
    status = '퇴사' if retire and retire <= TODAY else '재직'
    if status != '재직':
        continue

    h = next((hh for hh in r.get('history', []) if str(hh.get('year', '')) == YEAR), {})
    dept = (h.get('deptNm') or '').strip()
    hq   = (h.get('hqNm') or '').strip()
    div  = (h.get('divisionNm') or '').strip()
    rank = (h.get('statPositionNm') or '').strip()

    # _ui_dept
    if uno in TEST_UNOS:
        ui = 'Test'
    elif rank in EXEC_RANKS:
        ui = 'M-Level'
    else:
        ui = dept or hq or div or 'M-Level'

    # 부서_그룹
    if uno in TEST_UNOS:
        grp = 'Test'
    elif rank in EXEC_RANKS:
        grp = 'M-Level'
    elif dept in SHOW_AS_TEAM:
        grp = dept
    elif hq in SHOW_AS_HQ:
        grp = hq
    elif div:
        grp = div
    elif hq:
        grp = hq
    else:
        grp = 'M-Level'

    rows.append({'name': name, 'uno': uno, 'dept': dept, 'hq': hq,
                 'div': div, 'rank': rank, 'grp': grp})

df = pd.DataFrame(rows)

# 제외 그룹 제외
df_filt = df[~df['grp'].isin(exclude_groups)].copy()

print(f'=== 재직자 전체: {len(df)}명 / 제외 후: {len(df_filt)}명 ===\n')

# ── 1. 직급 분포 전체 ──
print('=== 직급 분포 (제외 후 재직자) ===')
rank_counts = df_filt['rank'].value_counts()
rank_order_set = set(config.RANK_ORDER)
for rank, cnt in rank_counts.items():
    tag = '' if rank in rank_order_set else '  ★ 비표준 (피벗에서 누락)'
    print(f'  {cnt:3d}명  {rank!r}{tag}')

# ── 2. 사업부별 실제인원 vs 피벗 인원 ──
print('\n=== 사업부별 실제인원 vs 표준직급 인원 (피벗 합계) ===')
print(f'  {"부서_그룹":22s}  {"실제인원":6s}  {"표준직급인원":8s}  {"누락인원":6s}  누락자')
print('  ' + '-'*80)

grp_total = df_filt.groupby('grp').size()
grp_std   = df_filt[df_filt['rank'].isin(rank_order_set)].groupby('grp').size()

for grp in sorted(grp_total.index):
    total = grp_total.get(grp, 0)
    std   = grp_std.get(grp, 0)
    missing = total - std
    if missing > 0:
        missing_names = df_filt[(df_filt['grp'] == grp) & (~df_filt['rank'].isin(rank_order_set))][['name','rank']].values.tolist()
        missing_str = ', '.join(f'{n}({r})' for n,r in missing_names)
    else:
        missing_str = ''
    flag = '  ⚠' if missing > 0 else ''
    print(f'  {grp:22s}  {total:6d}명  {std:8d}명  {missing:6d}명  {missing_str}{flag}')

# -*- coding: utf-8 -*-
"""퇴사자 _eff_ 컬럼 및 fallback 결과 확인"""
import sys, os, tomllib, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import data
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

# _build_users_df 결과 확인
df_raw = data._build_users_df(records)
retired_raw = df_raw[df_raw['재직상태'] == '퇴사'].copy()
print(f'=== 퇴사자 전체: {len(retired_raw)}명 ===')
print()
print('[_eff_ 컬럼 샘플 — _build_users_df 직후]')
print(f'  {"이름":10s} {"퇴사일":12s} {"_eff_dept":20s} {"_eff_hq":20s} {"_eff_rank":12s}')
print('  ' + '-'*80)
for _, row in retired_raw.head(15).iterrows():
    print(f'  {row["임직원명"]:10s} {row["퇴사일자"]:12s} {row["_eff_deptNm"]:20s} {row["_eff_hqNm"]:20s} {row["_eff_rankNm"]:12s}')

print()

# run_all 후 map_all 결과 확인
import pandas as pd
df_users, df_login, df_download, df_proposal = data.load_from_api()
df_users, df_login, df_download, df_proposal = data.preprocess_all(df_users, df_login, df_download, df_proposal)
df_users, df_login, df_download, df_proposal = data.map_all(df_users, df_login, df_download, df_proposal)
df_users = data.add_rank_group(df_users)

retired_mapped = df_users[df_users['재직상태'] == '퇴사'].copy()
print(f'[map_all 적용 후 퇴사자 부서_그룹 분포]')
grp_dist = retired_mapped['부서_그룹'].value_counts()
for grp, cnt in grp_dist.items():
    print(f'  {cnt:3d}명  {grp}')

print()
print('[퇴사자 상세 (이름 / 직급 / 부서 / 부서_그룹 / _ui_dept)]')
print(f'  {"이름":10s} {"직급":8s} {"부서":20s} {"부서_그룹":20s} {"_ui_dept":20s}')
print('  ' + '-'*90)
for _, row in retired_mapped.sort_values('부서_그룹').iterrows():
    print(f'  {row["임직원명"]:10s} {row["직급"]:8s} {str(row["부서"]):20s} {str(row["부서_그룹"]):20s} {str(row["_ui_dept"]):20s}')

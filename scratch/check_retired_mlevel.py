# -*- coding: utf-8 -*-
"""퇴사자 중 M-Level로 남아있는 사람 확인"""
import sys, os, tomllib, requests
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config, data

secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
with open(secrets_path, 'rb') as f:
    secrets = tomllib.load(f)
TOKEN = secrets.get('api', {}).get('token', '')
HEADERS = {'Content-Type': 'application/json', 'Authorization': f'Bearer {TOKEN}'}
resp = requests.get(config.API_BASE_URL + config.API_ENDPOINT_USERS, headers=HEADERS, verify=False, timeout=30)
records = resp.json()
if isinstance(records, dict):
    records = records.get('data', {}).get('list', records.get('list', []))

df_users, df_login, df_download, df_proposal = data.load_from_api()
df_users, df_login, df_download, df_proposal = data.preprocess_all(df_users, df_login, df_download, df_proposal)
df_users, df_login, df_download, df_proposal = data.map_all(df_users, df_login, df_download, df_proposal)

retired_mlevel = df_users[
    (df_users['재직상태'] == '퇴사') &
    (df_users['부서_그룹'] == 'M-Level')
].copy()

print(f'=== 퇴사자 중 M-Level: {len(retired_mlevel)}명 ===')
print(f'  {"이름":10s} {"UserNo":8s} {"직급":12s} {"_eff_deptNm":20s} {"_eff_hqNm":20s} {"_eff_rankNm":12s} {"퇴사일자":12s}')
print('  ' + '-'*100)
for _, r in retired_mlevel.iterrows():
    eff_dept = str(r.get('_eff_deptNm', ''))
    eff_hq   = str(r.get('_eff_hqNm', ''))
    eff_rank = str(r.get('_eff_rankNm', ''))
    print(f'  {r["임직원명"]:10s} {r["UserNo"]:8s} {r["직급"]:12s} {eff_dept:20s} {eff_hq:20s} {eff_rank:12s} {r["퇴사일자"]:12s}')

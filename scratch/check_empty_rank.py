# -*- coding: utf-8 -*-
"""재직자 중 직급/사업부 비어있는 사람 확인"""
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

df_users, *_ = data.load_from_api()
df_users, *_ = data.preprocess_all(df_users, *[__import__('pandas').DataFrame()]*3)
df_users, *_ = data.map_all(df_users, *[__import__('pandas').DataFrame()]*3)
df_users = data.add_rank_group(df_users)

# 재직자만
active = df_users[df_users['재직상태'] == '재직'].copy()

null_vals = {'', 'nan', 'NaN', 'None', '정보미등록'}

print(f'=== 재직자 전체: {len(active)}명 ===\n')

# 직급 비어있는 재직자
empty_rank = active[active['직급'].astype(str).str.strip().isin(null_vals)]
print(f'[직급 비어있는 재직자: {len(empty_rank)}명]')
for _, r in empty_rank.iterrows():
    print(f'  UserNo={r["UserNo"]}  이름={r["임직원명"]}  직급={r["직급"]!r}  부서={r["부서"]}  부서_그룹={r["부서_그룹"]}  _eff_rank={r.get("_eff_rankNm","")!r}')

print()

# 사업부 비어있는 재직자
empty_div = active[active['사업부'].astype(str).str.strip().isin(null_vals)]
print(f'[사업부 비어있는 재직자: {len(empty_div)}명]')
for _, r in empty_div.iterrows():
    print(f'  UserNo={r["UserNo"]}  이름={r["임직원명"]}  직급={r["직급"]}  사업부={r["사업부"]!r}  부서_그룹={r["부서_그룹"]}')

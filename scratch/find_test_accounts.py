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

# 테스트 계정으로 의심되는 이름 목록
TEST_NAMES = [
    '연구소업무활동',
    '신규임원(사업부장) OT용',
    '신규임원(사업부장)OT용',
    '마스터관리자',
    '마스터관리자2',
    'AXDX 테스트 계정',
    'AXDX테스트계정',
]

print('=== 테스트 계정 UserNo 조회 ===')
for r in records:
    nm = r.get('userNm', '') or ''
    if any(t in nm for t in TEST_NAMES) or nm in TEST_NAMES:
        retire = r.get('retireDt') or ''
        uno = r.get('userNo', '')
        prs = r.get('prsId', '')
        h2026 = next((h for h in r.get('history', []) if str(h.get('year',''))=='2026'), {})
        div_  = h2026.get('divisionNm') or ''
        rank_ = h2026.get('statPositionNm') or ''
        print(f"  UserNo={str(uno).zfill(3)}  prsId={prs!r:30s}  name={nm!r:30s}  div={div_:20s}  rank={rank_:12s}  retire={retire!r}")

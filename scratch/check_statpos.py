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

rows = []
for r in records:
    retire = r.get('retireDt') or ''
    if retire:
        continue  # 재직자만
    for h in r.get('history', []):
        if str(h.get('year', '')) == '2026':
            rows.append({
                'name':    r.get('userNm', ''),
                'div':     h.get('divisionNm') or '',
                'hq':      h.get('hqNm') or '',
                'dept':    h.get('deptNm') or '',
                'rank':    h.get('statPositionNm') or '',
            })

RANK_ORDER = set(config.RANK_ORDER)

from collections import Counter

# 전체 statPositionNm 분포
print('=== 전체 statPositionNm 분포 (2026 재직자) ===')
rank_cnt = Counter(r['rank'] for r in rows)
for rank, cnt in sorted(rank_cnt.items(), key=lambda x: -x[1]):
    tag = '' if rank in RANK_ORDER else '  ← 비표준'
    print(f'  {cnt:3d}명  {rank!r}{tag}')

# 비표준 직급 직원 상세
non_std = [r for r in rows if r['rank'] not in RANK_ORDER]
print()
print(f'=== 비표준 직급 직원 상세 ({len(non_std)}명) ===')
for r in sorted(non_std, key=lambda x: (x['rank'], x['div'])):
    print(f"  {r['name']:8s} | rank={r['rank']:12s} | div={r['div']:20s} | hq={r['hq']:20s} | dept={r['dept']}")

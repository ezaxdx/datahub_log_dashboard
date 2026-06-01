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
    for h in r.get('history', []):
        if str(h.get('year', '')) == '2026':
            rows.append({
                'name':   r.get('userNm', ''),
                'status': '퇴사' if retire else '재직',
                'div':    h.get('divisionNm') or '',
                'hq':     h.get('hqNm') or '',
                'dept':   h.get('deptNm') or '',
                'rank':   h.get('statPositionNm') or '',
            })

active = [r for r in rows if r['status'] == '재직']

# Q1. 디지털융합혁신부 상세
print('=== Q1. 디지털융합혁신부 전체 상세 ===')
for r in sorted(active, key=lambda x: (x['hq'], x['dept'])):
    if r['div'] == '디지털융합혁신부':
        print(f"  {r['name']:8s} | hqNm={r['hq']:22s} | deptNm={r['dept']:22s} | rank={r['rank']}")

# Q3. 서울스피커스뷰로
print()
print('=== Q3. 서울스피커스뷰로 직원 목록 ===')
for r in active:
    if '서울스피커스' in r['div']:
        print(f"  {r['name']:8s} | hqNm={r['hq']:22s} | deptNm={r['dept']:22s} | rank={r['rank']}")

# Q4. MICE부문 + hqNm 없는 직원
print()
print('=== Q4. MICE부문 hqNm 없는 직원 ===')
found = False
for r in active:
    if r['div'] == 'MICE부문' and not r['hq']:
        print(f"  {r['name']:8s} | deptNm={r['dept']:22s} | rank={r['rank']}")
        found = True
if not found:
    print('  (없음)')

# Q5. I-nori 통계직급
print()
print('=== Q5. I-nori사업부 통계직급 현황 ===')
from collections import Counter
inori = [r for r in active if r['div'] == 'I-nori사업부']
rank_cnt = Counter(r['rank'] for r in inori)
for rank, cnt in sorted(rank_cnt.items(), key=lambda x: -x[1]):
    print(f"  {cnt:2d}명 | {rank!r}")
print('  --- 상세 ---')
for r in sorted(inori, key=lambda x: (x['hq'], x['rank'])):
    print(f"  {r['name']:8s} | hqNm={r['hq']:22s} | rank={r['rank']}")

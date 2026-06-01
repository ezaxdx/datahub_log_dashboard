# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tomllib, requests
import config

secrets_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.streamlit', 'secrets.toml')
with open(secrets_path, 'rb') as f:
    secrets = tomllib.load(f)

BASE_URL = config.API_BASE_URL
TOKEN = secrets.get("api", {}).get("token", "")
HEADERS = {"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"}

resp = requests.get(BASE_URL + config.API_ENDPOINT_USERS, headers=HEADERS, verify=False, timeout=30)
data = resp.json()
records = data if isinstance(data, list) else data.get("data", {}).get("list", data.get("list", []))

# 2026 hqNm 전체 목록
hq_set = set()
div_set = set()
dept_set = set()
for r in records:
    for h in r.get("history", []):
        if str(h.get("year","")) == "2026":
            hq_set.add(h.get("hqNm","") or "")
            div_set.add(h.get("divisionNm","") or "")
            dept_set.add(h.get("deptNm","") or "")

print("=== 2026 divisionNm (사업부) 전체 ===")
for v in sorted(div_set): print(f"  {v!r}")

print()
print("=== 2026 hqNm (본부/실) 전체 ===")
for v in sorted(hq_set): print(f"  {v!r}")

print()
print("=== 2026 deptNm (팀) 전체 - 디지털마케팅/IP솔루션 포함 여부 ===")
for v in sorted(dept_set):
    if any(kw in v for kw in ['디지털마케팅', 'IP솔루션', '디지털', 'IP']):
        print(f"  ★ {v!r}")
    else:
        print(f"    {v!r}")

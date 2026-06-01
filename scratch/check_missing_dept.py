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

# 찾을 이름 목록
names = ["조수아", "김미선", "강민구", "조민경", "류두영", "김소희", "이해림"]

for r in records:
    nm = r.get("userNm", "")
    if nm in names:
        print(f"\n=== {nm} (userNo={r.get('userNo')}) ===")
        print(f"  retireDt: {r.get('retireDt')}")
        hist = r.get("history", [])
        if not hist:
            print("  history: 없음")
        for h in hist:
            print(f"  year={h.get('year')} | deptNm={h.get('deptNm')!r} | hqNm={h.get('hqNm')!r} | divisionNm={h.get('divisionNm')!r} | statPositionNm={h.get('statPositionNm')!r}")

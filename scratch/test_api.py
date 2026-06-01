"""
API 연결 테스트 스크립트
실행: python scratch/test_api.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import tomllib
import config

# secrets.toml 에서 토큰 로드
secrets_path = os.path.join(".streamlit", "secrets.toml")
token = ""
if os.path.exists(secrets_path):
    with open(secrets_path, "rb") as f:
        sec = tomllib.load(f)
    token = sec.get("api", {}).get("token", "")

headers = {"Content-Type": "application/json"}
if token:
    headers["Authorization"] = token if token.startswith("Bearer ") else f"Bearer {token}"

base_url   = config.API_BASE_URL
verify_ssl = config.API_VERIFY_SSL

print("=" * 60)
print(f"Base URL : {base_url}")
print(f"Token    : {'설정됨 (' + token[:20] + '...)' if token else '없음 ❌'}")
print("=" * 60)

def test_endpoint(label, path, method="POST", body=None):
    url = base_url + path
    print(f"\n▶ [{label}]  {method} {path}")
    try:
        if method == "POST":
            resp = requests.post(url, json=body or {"page": 0, "size": 3},
                                 headers=headers, verify=verify_ssl, timeout=15)
        else:
            resp = requests.get(url, params={"page": 0, "size": 3},
                                headers=headers, verify=verify_ssl, timeout=15)

        print(f"  HTTP {resp.status_code}")
        if resp.status_code == 200:
            j = resp.json()
            # 레코드 수 파악
            if isinstance(j, list):
                print(f"  ✅ 응답: 배열 {len(j)}건")
            elif "data" in j and isinstance(j["data"], dict):
                cnt = j["data"].get("totalCount", "?")
                sample = j["data"].get("list", [])[:1]
                print(f"  ✅ 응답: totalCount={cnt}")
                if sample:
                    print(f"  샘플 키: {list(sample[0].keys())}")
            elif "list" in j:
                cnt = j.get("totalCount", len(j["list"]))
                sample = j["list"][:1]
                print(f"  ✅ 응답: totalCount={cnt}")
                if sample:
                    print(f"  샘플 키: {list(sample[0].keys())}")
            else:
                print(f"  ✅ 응답 키: {list(j.keys())}")
        elif resp.status_code == 401:
            print("  ❌ 401 Unauthorized — 토큰 만료 또는 잘못된 토큰")
        elif resp.status_code == 403:
            print("  ❌ 403 Forbidden — 권한 없음")
        elif resp.status_code == 404:
            print("  ❌ 404 Not Found — 경로 확인 필요")
        else:
            print(f"  ⚠️  {resp.text[:200]}")
    except Exception as e:
        print(f"  ❌ 연결 실패: {e}")

test_endpoint("직원정보",   config.API_ENDPOINT_USERS,    method="GET")
test_endpoint("로그인",    config.API_ENDPOINT_LOGIN,    method="POST")
test_endpoint("다운로드",  config.API_ENDPOINT_DOWNLOAD, method="POST")
test_endpoint("제안서",    config.API_ENDPOINT_PROPOSAL, method="POST", body={})

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)

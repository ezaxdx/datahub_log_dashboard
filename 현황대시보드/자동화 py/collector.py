import requests
import urllib3
import pandas as pd
import json
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- API 세션 설정 ---
PHPSESSID = "tsl0ffuqaoavftcu6p11sqo5hg"

# --- Google Sheets 인증 설정 ---
def load_credentials():
    import tomllib
    # .streamlit/secrets.toml 위치 (상위 폴더에 있는 경우 고려)
    secrets_path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml")
    
    if os.path.exists(secrets_path):
        with open(secrets_path, "rb") as f:
            secrets = tomllib.load(f)
            if "gcp_service_account" in secrets:
                print("secrets.toml에서 인증 정보를 로드했습니다.")
                return (
                    Credentials.from_service_account_info(secrets["gcp_service_account"], scopes=scope),
                    secrets.get("gcp_sheet_url")
                )
    
    # Fallback: 기존 로컬 JSON 키 파일 (만약의 경우 대비)
    json_path = r"C:\김연아\@ AXDX팀\1. 로그인, 다운로드 대시보드 제작\@micedx1계정api키정보\ezdatahub-log-5a89069d212c.json"
    if os.path.exists(json_path):
        print("로컬 JSON 파일에서 인증 정보를 로드했습니다.")
        return (
            Credentials.from_service_account_file(json_path, scopes=scope),
            "https://docs.google.com/spreadsheets/d/1N0UUF2Qroqbukd37WRgur2FpjzxEXLevT79EB_GutEk/edit?usp=sharing"
        )
    
    raise FileNotFoundError("인증 정보(secrets.toml 또는 JSON 키)를 찾을 수 없습니다.")

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 인증 실행
creds, SPREADSHEET_URL = load_credentials()
gc = gspread.authorize(creds)
doc = gc.open_by_url(SPREADSHEET_URL)


# =============================================
# 1. 다운로드 로그 수집
# =============================================

print("=== 다운로드 로그 수집 시작 ===")

# checkpoint 읽기
dl_checkpoint_file = "last_download_log_no.txt"
if os.path.exists(dl_checkpoint_file):
    with open(dl_checkpoint_file, "r") as f:
        last_dl_log = int(f.read().strip())
else:
    last_dl_log = 0

print("이전 마지막 download log_no:", last_dl_log)

# API 호출
dl_url = "https://ictwbs.ezpmp.co.kr/ict.wbs/api/micedx.download.list.php"
dl_headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://ictwbs.ezpmp.co.kr/ict.wbs/micedx.download.list.php",
    "Cookie": f"PHPSESSID={PHPSESSID}"
}
dl_payload = {
    "searchStartDate": "2024-01-01",
    "searchEndDate": datetime.today().strftime("%Y-%m-%d"),
    "page": 1,
    "rows": 1000
}

dl_response = requests.post(dl_url, headers=dl_headers, data=json.dumps(dl_payload), verify=False)

if dl_response.status_code != 200:
    print("다운로드 API 호출 실패:", dl_response.status_code)
else:
    dl_data = dl_response.json()
    df_dl = pd.DataFrame(dl_data.get("rows", []) if isinstance(dl_data, dict) else dl_data)

    if df_dl.empty:
        print("다운로드 데이터 없음")
    else:
        # 신규 데이터 필터
        df_dl["log_no"] = pd.to_numeric(df_dl["log_no"], errors="coerce")
        df_dl = df_dl.sort_values("log_no")
        df_dl = df_dl[df_dl["log_no"] > last_dl_log]

        print("다운로드 신규 데이터 수:", len(df_dl))

        if not df_dl.empty:
            # 데이터 가공
            cols_to_drop = ["temp2", "temp3", "temp4", "temp5"]
            df_dl = df_dl.drop(columns=[c for c in cols_to_drop if c in df_dl.columns])

            if "file_size" in df_dl.columns:
                df_dl["file_size"] = pd.to_numeric(df_dl["file_size"], errors="coerce")
                df_dl["크기"] = (df_dl["file_size"] / (1024 * 1024)).round(2).astype(str) + " MB"
                df_dl = df_dl.drop(columns=["file_size"])

            if "create_dt" in df_dl.columns:
                df_dl["create_dt"] = pd.to_datetime(df_dl["create_dt"], errors="coerce")
                df_dl["다운로드 일자"] = df_dl["create_dt"].dt.date.astype(str)
                df_dl["다운로드 시간"] = df_dl["create_dt"].dt.time.astype(str)
                df_dl = df_dl.drop(columns=["create_dt"])

            def get_category(path):
                if pd.isna(path): return ""
                if "project-search" in str(path): return "프로젝트 찾기"
                elif "manage-file" in str(path): return "운영자료 찾기"
                elif "support" in str(path): return "서포트 센터"
                return ""

            df_dl["기타"] = df_dl["temp1"].apply(get_category)

            rename_dict = {
                "log_no": "No",
                "file_nm": "파일명",
                "ip_addr": "IP",
                "temp1": "경로",
                "userNo": "user No",
                "userId": "사용자ID",
                "userNm": "이름",
                "divisionNm": "부서",
                "departmentNm": "팀",
                "jobNm": "역할"
            }
            df_dl = df_dl.rename(columns=rename_dict)

            final_columns = ["No", "파일명", "크기", "IP", "경로", "user No", "사용자ID",
                             "이름", "부서", "팀", "역할", "다운로드 일자", "다운로드 시간", "기타"]
            df_dl = df_dl[[c for c in final_columns if c in df_dl.columns]]
            df_dl = df_dl.fillna("")

            # Google Sheets 업로드
            worksheet_dl = doc.worksheet("download")
            existing_dl = worksheet_dl.get_all_values()
            start_row_dl = len(existing_dl) + 1
            worksheet_dl.update(f"A{start_row_dl}", df_dl.values.tolist())
            print("다운로드 Google Sheets 업로드 완료")

            # checkpoint 업데이트
            max_dl_log = int(df_dl["No"].dropna().max())
            with open(dl_checkpoint_file, "w") as f:
                f.write(str(max_dl_log))
            print("다운로드 checkpoint 업데이트:", max_dl_log)


# =============================================
# 2. 로그인 로그 수집
# =============================================

print("=== 로그인 로그 수집 시작 ===")

# checkpoint 읽기
login_checkpoint_file = "last_login_log_no.txt"
if os.path.exists(login_checkpoint_file):
    with open(login_checkpoint_file, "r") as f:
        last_login_log = int(f.read().strip())
else:
    last_login_log = 0

print("이전 마지막 login log_no:", last_login_log)

# API 호출
login_url = "https://ictwbs.ezpmp.co.kr/ict.wbs/api/micedx.loginhistory.list.php"
login_headers = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/javascript, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://ictwbs.ezpmp.co.kr/ict.wbs/micedx.loginhistory.list.php",
    "Cookie": f"PHPSESSID={PHPSESSID}"
}
login_payload = {
    "searchStartDate": "2024-01-01",
    "searchEndDate": datetime.today().strftime("%Y-%m-%d"),
    "page": 1,
    "rows": 1000
}

login_response = requests.post(login_url, headers=login_headers, data=json.dumps(login_payload), verify=False)

if login_response.status_code != 200:
    print("로그인 API 호출 실패:", login_response.status_code)
else:
    login_data = login_response.json()
    df_login = pd.DataFrame(login_data if isinstance(login_data, list) else login_data.get("rows", []))

    if df_login.empty:
        print("로그인 데이터 없음")
    else:
        # 신규 데이터 필터
        df_login["login_no"] = pd.to_numeric(df_login["login_no"], errors="coerce")
        df_login = df_login[df_login["login_no"] > last_login_log]

        print("로그인 신규 데이터 수:", len(df_login))

        if not df_login.empty:
            # 데이터 가공
            cols_to_drop = ["project_cd", "site_id", "nat_nm", "reg_nm", "city_nm", "job_nm"]
            df_login = df_login.drop(columns=[c for c in cols_to_drop if c in df_login.columns])

            if "created_dt" in df_login.columns:
                df_login["created_dt"] = pd.to_datetime(df_login["created_dt"], errors="coerce")
                df_login["로그인 일자"] = df_login["created_dt"].dt.strftime("%Y-%m-%d")
                df_login["로그인 시간"] = df_login["created_dt"].dt.strftime("%H:%M:%S")
                df_login = df_login.drop(columns=["created_dt"])

            rename_dict = {
                "login_no": "NO",
                "user_no": "UserNo",
                "ip_address": "IP",
                "user_agent": "브라우저",
                "device_gbn": "디바이스",
                "os_nm": "OS",
                "browser_nm": "브라우저2",
                "user_nm": "이름",
                "department_nm": "부서",
                "position_nm": "직급"
            }
            df_login = df_login.rename(columns=rename_dict)

            final_columns = ["NO", "UserNo", "이름", "부서", "직급", "nat_cd",
                             "IP", "브라우저", "디바이스", "OS", "브라우저2", "로그인 일자", "로그인 시간"]
            df_login = df_login[[c for c in final_columns if c in df_login.columns]]
            df_login = df_login.fillna("")

            # Google Sheets 업로드
            worksheet_login = doc.worksheet("login")
            worksheet_login.append_rows(df_login.values.tolist())
            print("로그인 Google Sheets 업로드 완료")

            # checkpoint 업데이트
            no_series = df_login["NO"].dropna()
            if not no_series.empty:
                max_login_log = int(no_series.max())
                with open(login_checkpoint_file, "w") as f:
                    f.write(str(max_login_log))
                print("로그인 checkpoint 업데이트:", max_login_log)

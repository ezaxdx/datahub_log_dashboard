# config.py

# 연도 설정
CURRENT_YEAR = 2026
PREV_YEAR    = 2025

# 서비스 오픈 기준일 (D+카운터용)
BASE_DATE = "2025-01-17"

# 직원정보 시트: 연도별 컬럼명 패턴
YEAR_COL_DEPT = "{year}_부서명"
YEAR_COL_HQ   = "{year}_본부/실"
YEAR_COL_RANK = "{year}_통계 직급"
YEAR_COL_DIVISION = "{year}_사업부"

# 표준 이메일(ID) 컬럼명 (사용자 요청: PRS ID로 통일)
COL_NAME_EMAIL = "PRS ID"

# 시트 이름
SHEET_NAME_USERS    = "직원정보"
SHEET_NAME_LOGIN    = "login"
SHEET_NAME_DOWNLOAD = "download"
SHEET_NAME_PROPOSAL = "제안서_ezPDF"

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

# 부서별 현황 페이지 전용: 본부명으로 그대로 보여줄 부서 목록
DEPT_SHOW_AS_HQ = ["CP실", "주최사업실"]

# 직급 정렬 순서 (사원 -> 임원)
RANK_ORDER = ['사원', '대리', '과장', '차장', '팀장', '부장', '본부장', '임원']

# 표준 이메일(ID) 컬럼명 
COL_NAME_EMAIL = "PRS ID"

# 시트 이름
SHEET_NAME_USERS    = "직원정보"
SHEET_NAME_IGNORE   = "퇴사자_ignore"
SHEET_NAME_LOGIN    = "login"
SHEET_NAME_DOWNLOAD = "download"
SHEET_NAME_PROPOSAL = "제안서_ezPDF"

# 사이드바 기본 제외 대상 (초기 선택에서 제외, Select All 시 포함)
DEFAULT_EXCLUDE_DEPTS = ["AXDX팀", "ICT융합개발본부"]
DEFAULT_EXCLUDE_USERNO = ["곽은경_280"]

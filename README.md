# EZ데이터허브 로그 분석 대시보드

> EZ데이터허브 임직원 사용 로그를 수집·분석하는 내부 운영 대시보드입니다.

---

## 개요

| 항목 | 내용 |
|---|---|
| 서비스 오픈일 | 2025-01-17 |
| 배포 환경 | Streamlit Community Cloud |
| 데이터 저장소 | Google Sheets (서비스 계정 연동) |
| 데이터 수집 | 수동 수집 (폐쇄망 API, PHPSESSID 세션 기반) |
| 레포지토리 | ezaxdx/datahub_log_dashboard |
| 기준 브랜치 | main |

---

## 레포지토리 구조

```
현황대시보드/
├── .streamlit/
│   └── secrets.toml          # GCP 서비스 계정 및 Sheets URL (git 제외)
├── .github/
├── docs/                     # 스펙 문서
├── pages/
│   ├── 1_total.py            # Total Dashboard
│   ├── 2_File_Analysis.py    # File Analysis
│   ├── 3_department.py       # Dept & Team
│   ├── 4_kpi.py              # Check KPI
│   └── 5_employee_list.py    # Employee List
├── 자동화 py/                 # 데이터 수집 스크립트 (폐쇄망 API)
├── app.py                    # 메인 진입점, 사이드바 및 페이지 라우팅
├── config.py                 # 전역 설정 (연도, 시트명, 컬럼명 등)
├── data.py                   # 데이터 로드, 전처리, 조인 파이프라인
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 브랜치 구조

| 브랜치 | 용도 |
|---|---|
| main | 배포 브랜치 (Streamlit Cloud 연동) |
| Data_Refactor_v_1 | 데이터 레이어 및 멀티페이지 리팩토링 작업 브랜치 |
| review/before-mar26 | 3월 26일 이전 상태 보존 브랜치 |

---

## 데이터 파이프라인

```
폐쇄망 인트라넷 API
    ↓ (PHPSESSID 세션 인증)
자동화 py/ 수집 스크립트 (수동 실행)
    ↓ (pandas 전처리)
Google Sheets 누적 적재
    ↓ (gspread + 서비스 계정)
Streamlit 대시보드 (st.cache_data ttl=600)
```

> 수집 주기: 수동. 폐쇄망 API 특성상 GitHub Actions 자동화 불가.

---

## Google Sheets 구성

| 시트명 | 주요 컬럼 |
|---|---|
| 직원정보 | UserNo, 임직원명, PRS ID, 입사일자, (연도별) 사업부/본부실/부서명/직위/직급/통계직급 |
| 퇴사자_ignore | 직원정보와 동일 구조 + 퇴사월 |
| login | NO, UserNo, 이름, 부서, 직급, 로그인 일자, 로그인 시간 등 |
| download | NO, 파일명, UserNo, PRS ID, 경로 메뉴명, 다운로드 일자 등 |
| 제안서_ezPDF | 번호, 문서경로, PRS ID, 등록일, 이름, 팀, 역할 등 |

---

## 로컬 실행 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 인증 설정
`.streamlit/secrets.toml` 파일 생성:
```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
client_id = "..."

gcp_sheet_url = "https://docs.google.com/spreadsheets/d/..."
```

### 3. 실행
```bash
streamlit run app.py
```

---

## 환경 설정 (config.py 주요 항목)

| 설정 | 값 | 설명 |
|---|---|---|
| CURRENT_YEAR | 2026 | 현재 기준 연도 |
| PREV_YEAR | 2025 | 이전 연도 |
| BASE_DATE | 2025-01-17 | 서비스 오픈일 (D+ 카운터 기준) |
| DEFAULT_EXCLUDE_DEPTS | AXDX팀, ICT융합개발본부 | 사이드바 기본 제외 부서 |
| DEFAULT_EXCLUDE_USERNO | 곽은경_280 | 사이드바 기본 제외 사용자 |

---

## 주요 기능

- **Total Dashboard**: 로그인/다운로드 KPI 요약, 일자별 추이, 부서/직급별 TOP5
- **File Analysis**: 직원별 활동 상세, 제안서 경고 감지, 슬라이딩 윈도우 타임라인
- **Dept & Team**: 부서/직급별 사용현황 및 사용률 분석
- **Check KPI**: KPI 달성 현황 모니터링
- **Employee List**: 전체 재직자 목록 및 CSV 다운로드

---

## 데이터 수집 방법

`자동화 py/` 폴더 내 스크립트를 수동으로 실행합니다.
- 인트라넷 API에 PHPSESSID 세션으로 인증
- checkpoint 기반 신규 데이터만 추출 (중복 방지)
- Google Sheets에 append 방식으로 누적 적재
- 실행 시 로컬 Excel 백업 자동 저장
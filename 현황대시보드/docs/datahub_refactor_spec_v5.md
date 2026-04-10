# Datahub 로그 대시보드 리팩토링 명세서 v5

## 변경 이력

| 버전 | 주요 변경 |
|---|---|
| v4 | 초기 명세 |
| v5 | 3_file.py 삭제 및 2_user.py 병합, Total 차트 구성 변경, Department & Team 차트 구성 확정, 부서명 fallback 3단계 추가 |

---

## 목적

- app.py에 혼재된 데이터 처리 레이어를 완전 분리
- 매년 재사용 가능한 구조로 전환
- 다년도 데이터 비교 및 다중 페이지 네비게이션 지원

---

## 디렉토리 구조

```
config.py               연도/설정값 (매년 수정 위치)
data.py                 로드 + 매핑 + 전처리
app.py                  네비게이션 진입점 및 공통 데이터 로드

pages/
  1_total.py            Total Dashboard
  2_user.py             User (파일 분석 병합)
  3_department.py       Department & Team
  4_kpi.py              Check KPI
```

---

## 구축 순서

```
1단계 (완료)
  config.py
  data.py
  app.py
  pages/1_total.py

2단계 (진행 중)
  pages/1_total.py    차트 구성 수정
  pages/2_user.py     신규 작성
  pages/3_department.py  신규 작성

3단계 (2단계 완료 후)
  pages/4_kpi.py      KPI 정의 확정 후 별도 spec 작성
```

---

## config.py

매년 수정이 필요한 값 전체를 한 곳에 모음.
다른 파일에서 연도/날짜 값을 직접 하드코딩 금지.

```python
CURRENT_YEAR = 2026
PREV_YEAR    = 2025

# 서비스 오픈 기준일 (D+카운터용, 변경 없음)
BASE_DATE = "2025-01-17"

# 직원정보 시트: 연도별 컬럼명 패턴
YEAR_COL_DEPT     = "{year}_부서명"
YEAR_COL_HQ       = "{year}_본부/실"
YEAR_COL_DIVISION = "{year}_사업부"
YEAR_COL_RANK     = "{year}_통계 직급"

# 표준 이메일(ID) 컬럼명
COL_NAME_EMAIL = "PRS ID"

# 시트 이름
SHEET_NAME_USERS    = "직원정보"
SHEET_NAME_LOGIN    = "login"
SHEET_NAME_DOWNLOAD = "download"
SHEET_NAME_PROPOSAL = "제안서_ezPDF"
```

---

## 시트별 구조 정의

### 직원정보 (헤더 2행 병합 구조)
- row[0]: 연도 행 (병합셀, forward fill 처리)
- row[1]: 컬럼명 행
- 데이터: 3행부터
- 고정 컬럼: UserNo, 임직원명, PRS ID, 입사일자
- 연도별 컬럼: 부서명, 본부/실, 사업부, 직위, 직급 (평탄화 후 "2026_부서명" 형태)
- No 컬럼: 순번이므로 로드 시 제외
- 퇴사자 판별: CURRENT_YEAR 부서명이 빈칸이면 로드 시 제외
- 부서명 fallback 순서: 부서명 -> 본부/실 -> 사업부

### login
- 헤더: 1행
- 주요 컬럼: UserNo, 이름, 부서, 직급, 로그인 일자

### download
- 헤더: 1행
- 주요 컬럼: UserNo, 사용자ID(이메일), 다운로드 일자, 파일명, 경로 메뉴명

### 제안서_ezPDF
- 헤더: 1행
- UserNo 없음, 유저ID(이메일) 있음
- 주요 컬럼: 유저ID, 문서경로, 등록일

---

## Primary Key 규칙

- Primary Key: UserNo (3자리 zero-padding 문자열, ex. "001", "042")
- Secondary Key: 이메일 (제안서 시트처럼 UserNo 없는 경우에만 사용)
- 이름은 키로 사용 금지
- UserNo 임의 생성 금지
- 원본 데이터 수정 금지

---

## data.py 역할 및 규칙

내부적으로 load / map / preprocess 3개 함수 블록으로 구분.
외부에서는 load_all()과 run_all()만 호출.

### [load 블록]

**역할**
- Google Sheets 인증 및 연결
- 각 시트를 원본 그대로 DataFrame으로 반환
- 직원정보 헤더 평탄화: 2행 헤더를 "연도_컬럼명" 형태로 변환

**직원정보 헤더 평탄화 방식**
```
row[0]: ["", "", "2025", "2025", ..., "2026", "2026", ...]  <- 병합셀 forward fill 후
row[1]: ["UserNo", "임직원명", "부서명", "직급", ..., "부서명", "직급", ...]

결과: ["UserNo", "임직원명", "2025_부서명", "2025_직급", ..., "2026_부서명", "2026_직급", ...]
```
- 연도 셀 빈칸은 직전 값 이어받기 (forward fill)
- 고정 컬럼(UserNo, 임직원명, PRS ID, 입사일자)은 prefix 없이 그대로 사용

**규칙**
- 반환값은 원본 그대로 (정규화, 매핑, 컬럼 삭제 없음)
- 시트 없으면 빈 DataFrame 반환 (에러 raise 금지)
- 중복 컬럼명은 컬럼명+숫자로 자동 처리
- @st.cache_data(ttl=600) 적용

**공개 함수**
```
load_all() -> (df_users, df_login, df_download, df_proposal)
```

---

### [map 블록]

**역할**
- UserNo 3자리 zero-padding 정규화
- 이메일 -> UserNo 역매핑 (제안서 시트 전용)
- 각 로그 행의 year 값 기준으로 직원정보에서 이름/부서/직급 조인

**시트별 조인 전략**

| 시트 | UserNo | 이메일 | 조인 방법 |
|---|---|---|---|
| login | O | X | UserNo 기준 직접 조인 |
| download | O | O | UserNo 기준 직접 조인 |
| 제안서 | X | O | 이메일로 UserNo 역매핑 후 조인 |

**부서명 fallback (map 블록에서 처리)**
```python
d_val = df_u[dept_col]     if dept_col in df_u.columns else pd.Series([None] * len(df_u))
h_val = df_u[hq_col]       if hq_col   in df_u.columns else pd.Series([None] * len(df_u))
v_val = df_u[div_col]      if div_col  in df_u.columns else pd.Series([None] * len(df_u))
df_u["부서"] = d_val.fillna(h_val).fillna(v_val)
```

**연도별 마스터 분리**
```
각 로그 행의 year 컬럼 기준으로
year=2025 -> df_users의 "2025_부서명", "2025_직급" 참조
year=2026 -> df_users의 "2026_부서명", "2026_직급" 참조
```

**규칙**
- 조인 전 기존 이름/부서/직급 컬럼 삭제 후 마스터에서 재주입
- 조인 실패 행은 삭제하지 않고 해당 컬럼 빈값 유지
- 이름 기반 fallback 금지
- 직원정보 마스터는 UserNo 중복 제거 (첫 번째 행 기준)
- 이메일 빈값은 조인 전 NaN 처리 (카테시안 조인 방지)

---

### [preprocess 블록]

**역할**
- 날짜 컬럼을 date 컬럼으로 통일
- year 컬럼 추가 (date에서 자동 추출)
- 직급그룹 컬럼 추가
- 불필요 컬럼 제거

**날짜 컬럼 우선순위**
```
등록일 > 다운로드 일자 > 로그인 일자
```

**직급 그룹화 기준**
```
실무자(사원/대리): 사원, 대리, 주임, 연구원
관리자(차장↑): 차장, 팀장, 부장, 본부장, 이사, 실장, 수석, 상무, 전무
기타: 위 해당 없는 경우
```

**공개 함수**
```
run_all(df_users, df_login, df_download, df_proposal)
  -> (df_users, df_login, df_download, df_proposal)
```

---

## app.py 역할 및 규칙

**역할**
- data.py 호출하여 공통 데이터 로드
- 처리된 DataFrame을 st.session_state에 저장
- 페이지 네비게이션 설정

**규칙**
- 데이터 로드는 여기서 한 번만 수행
- merge, 매핑, 컬럼 처리 금지

---

## 공통 레이아웃

### 사이드바 구성 (전 페이지 공통)

```
최신 데이터 동기화
  - 클릭 시 Google Sheets 최신 데이터로 갱신

오픈한지 D-DAY
  - 서비스 오픈 기준일(BASE_DATE) 기준 경과일 표시
  - 최근 로그 날짜 표시

필터 (날짜 / 부서 / 직급)
  날짜 빠른 선택: 오늘 / 최근 1주일 / 전체 / 직접 지정
  부서 선택: multiselect
  직급 선택: multiselect

네비게이션
  - Total Dashboard
  - File Analysis
  - Department & Team
  - Check KPI
  - Employee List
      표 형태, 정렬 가능
      컬럼: UserNo / 이름 / 부서 / 직위 / 직급 / 이메일
      현재 필터 조건 기준 재직자 목록
```

### 페이지 상단 공통

```
{CURRENT_YEAR}년 EZ데이터허브 {페이지명} 대시보드
{CURRENT_YEAR}년 EZ데이터허브의 {설명문}을 확인할 수 있습니다.
```

---

## pages 구성

### pages/1_total.py - Total Dashboard

**목적**: 전체 현황 요약

**KPI (상단 5개 카드)**
```
총 로그인 수 | 제안서 다운로드 수 | 프로젝트 찾기 | 운영자료 찾기 | 서포트 센터
```

**차트 1행 (2열)**
```
좌: 일자별 활동 현황
    라인차트, 이중 y축
    선1: 로그인 추이 (좌측 y축)
    선2: 다운로드 합계 - sum(제안서 다운로드, 프로젝트 찾기, 운영자료 찾기, 서포트센터) (우측 y축)

우: 제안서 다운로드 경고 직원 리스트
    표 형태
    컬럼: UserNo / 이름 / 부서 / 직급 / 횟수
    경고 기준치 이상 다운로드 직원만 표시
    경고 기준치: session_state의 warning_threshold 사용
```

**차트 2행 (2열)**
```
차트 2행 (4열, 한 줄)
1: 부서별 로그인 건수 도넛
2: 부서별 다운로드 사용률 도넛  (순사용자 / 부서인원수 * 100)
3: 직급별 로그인 건수 도넛
4: 직급별 다운로드 사용률 도넛  (순사용자 / 직급인원수 * 100)

부서별/직급별 인원수 계산
  - 출처: st.session_state['df_users']
  - 계산: df_users.groupby('부서')['UserNo'].nunique()

다운로드 사용률 계산식
  - 순사용자 수 / 부서 인원수 * 100
  - 순사용자 기준: 해당 필터 기간 내 1회 이상 다운로드한 고유 UserNo 수

로그인은 건수 절대값 사용 (사용률 아님)

```

### pages/2_user.py - User

**목적**: 사용자별 활동 분석 및 파일 다운로드 현황 모니터링

**페이지 내부 필터**
```
모니터링 기준치: number_input (기본값 10)
  - 제안서 열람 현황의 기준치 초과 판단에 사용
  - warning_threshold로 session_state 저장
```

**섹션 1: 직원별 활동 상세내역 + 제안서 열람 현황 (2열)**

좌측 (넓게):
```
직원별 활동 상세내역 표
컬럼: UserNo / 이름 / 부서 / 직급 / 총로그인수 / 제안서다운로드 / 프로젝트찾기 / 운영자료찾기 / 서포트센터
정렬: 총로그인수 기준 내림차순
전체 필터(날짜/부서/직급) 적용
```

우측 (좁게):
```
제안서 열람 현황
현재 필터 조건 기준 총 n명 표시
기준치 초과 직원 리스트 (클릭 가능)
  - 클릭 시 하단 다운로드 타임라인 연동
기준치 초과 직원 없을 경우: "기준치를 초과하는 직원이 없습니다." 표시
```

**섹션 2: 다운로드 타임라인**
```
시간 단위 선택: 1시간 단위 (페이지 내부 필터)
표 형태
컬럼: UserNo / 이름 / 부서 / 직급 / PRS ID / 제안서 다운로드 수 / 문서이름
문서이름 출처: 제안서_ezPDF 시트의 문서경로 컬럼
제안서 열람 현황에서 직원 미선택 시: 전체 표시
직원 선택 시: 해당 직원 데이터만 표시
전체 필터(날짜/부서/직급) 적용
```

**섹션 3: 다운로드 현황 (4열)**

```
검색 프로젝트 top10
  출처: 제안서_ezPDF 시트 문서경로 파싱
  파싱 정규식: re.search(r'/(\d{6})\[([^\]]+)\]', str(path))
  컬럼: 프로젝트코드 / 프로젝트명 / 횟수
  전체 필터 적용

제안서 top10
  출처: 제안서_ezPDF 시트 문서경로
  문서경로에서 파일명 추출 (마지막 / 이후)
  컬럼: 제안서이름 / 횟수
  전체 필터 적용

운영자료 top10
  출처: download 시트
  조건: 경로 메뉴명에 "운영자료" 포함
  컬럼: 파일명 / 경로메뉴명 / 횟수
  전체 필터 적용

서포트센터 top10
  출처: download 시트
  조건: 경로 메뉴명에 "서포트" 포함
  컬럼: 파일명 / 경로메뉴명 / 횟수
  전체 필터 적용
```

---

### pages/3_department.py - Department & Team

**목적**: 부서 및 직급별 사용 현황 분석

**페이지 내부 필터**
```
우측 상단 드롭박스 (로그 종류 선택)
선택지: 로그인 / 제안서 / 다운로드 전체 / 프로젝트 찾기 / 운영자료 찾기 / 서포트센터
적용 범위: 부서별 사용률 차트, 직급별 사용률 차트만 변경
전체 필터(날짜/부서/직급)와 독립적으로 동작
```

**섹션 1: 부서별 사용률 (2열)**
```
좌: 라인그래프
    x축: 날짜
    y축: 횟수
    선 구분: 대리/사원 그룹 vs 차장이상 그룹
    드롭박스 선택 기준으로 데이터 변경

우: 막대그래프
    x축: 부서명
    y축: 횟수
    막대 구분: 대리/사원 그룹 vs 차장이상 그룹 (grouped)
    드롭박스 선택 기준으로 데이터 변경
    퍼센테이지 표시
```

**섹션 2: 직급별 사용률 (2열)**
```
좌: 막대그래프
    x축: 직급 (사원/대리/차장/팀장/부장/본부장 등 실제 존재하는 직급 전체)
    y축: 횟수
    드롭박스 선택 기준으로 데이터 변경

우: 라인그래프
    x축: 날짜
    y축: 횟수
    선 구분: 대리/사원 그룹 vs 차장이상 그룹
    드롭박스 선택 기준으로 데이터 변경
```

**섹션 3: 부서/직급별 인원 (2열)**
```
좌: 부서/직급별 인원 표
    출처: df_users (raw 직원현황)
    전체 필터 적용

우: 미정
```

---

### pages/4_kpi.py - Check KPI

날짜 필터 미적용.
3단계에서 별도 spec 작성 예정.

---

## 전체 처리 흐름

```
Google Sheets
    |
data.py: load_all()
    |  직원정보 헤더 평탄화 ("연도_컬럼명")
    |  각 시트 원본 로드
    v
data.py: run_all()
    |  preprocess: date, year, 직급그룹 컬럼 추가
    |  map: year 기준 부서/직급 조인
    |  부서명 fallback: 부서명 -> 본부/실 -> 사업부
    v
app.py: st.session_state 저장
    |
    +-- pages/1_total.py        날짜/부서/직급 필터 -> 전체 요약
    +-- pages/2_user.py         날짜/부서/직급 필터 -> 사용자/파일 분석
    +-- pages/3_department.py   날짜/부서/직급 필터 + 로그종류 -> 부서 분석
    +-- pages/4_kpi.py          필터 없음 -> KPI 현황
    +-- 직원 리스트             현재 필터 기준 재직자 목록
```

---

## 예외 처리 기준

| 상황 | 처리 방법 |
|---|---|
| UserNo 없는 행 (제안서 외) | 이름/부서/직급 빈값 유지, 행 삭제 금지 |
| 이메일 매핑 실패 (제안서) | 이름/부서/직급 빈값 유지, 행 삭제 금지 |
| 시트 없음 | 빈 DataFrame 반환 |
| 날짜 파싱 실패 | errors='coerce' 처리 (NaT) |
| 직원정보 중복 UserNo | 첫 번째 행 사용 |
| 해당 연도 부서 컬럼 없음 | 빈값 유지 |
| 부서명 빈값 | 본부/실 -> 사업부 순으로 fallback |
| 문서경로 파싱 실패 | 프로젝트코드/프로젝트명 None 처리 |
| 기준치 초과 직원 없음 | "기준치를 초과하는 직원이 없습니다." 표시 |

---

## 매년 유지보수 포인트

수정 위치는 config.py 한 곳.

```python
CURRENT_YEAR = 2027   # 변경
PREV_YEAR    = 2026   # 변경
BASE_DATE    = "2025-01-17"  # 변경 없음
```

직원정보 시트에 2027년 컬럼 추가 시 loader 자동 인식, 코드 수정 불필요.

---

## 금지 정책 요약

- UserNo 임의 생성 금지
- 이름 기반 매핑/fallback 금지
- 원본 데이터 직접 수정 금지
- app.py, pages/*.py 에서 merge/매핑/컬럼 처리 금지
- data.py 에서 st.* 호출 금지
- config.py 외 파일에서 연도/날짜 하드코딩 금지

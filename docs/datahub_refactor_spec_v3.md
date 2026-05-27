# Datahub 로그 대시보드 리팩토링 명세서 v3

## 목적

- app.py에 혼재된 데이터 처리 레이어를 완전 분리
- 매년 재사용 가능한 구조로 전환
- 다년도 데이터 비교 및 다중 페이지 네비게이션 지원

---

## 디렉토리 구조

```
config.py           연도/설정값 (매년 수정 위치)
data.py             로드 + 매핑 + 전처리 (데이터 구조 변경 시 수정)
app.py              네비게이션 진입점 및 공통 데이터 로드

pages/
  1_total.py        Total Dashboard
  2_user.py         User
  3_department.py   Department & Team
  4_file.py         File
  5_kpi.py          Check KPI
```

---

## 구축 순서

```
1단계 (현재)
  config.py
  data.py
  app.py
  pages/1_total.py    기존 app.py UI 이관

2단계 (1단계 데이터 정합성 확인 후)
  pages/2_user.py
  pages/3_department.py
  pages/4_file.py
  pages/5_kpi.py
```

2단계는 data.py가 안정적으로 동작한 이후 별도 spec 작성.

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
# loader가 헤더 평탄화 시 생성하는 키와 일치해야 함
YEAR_COL_DEPT = "{year}_부서명"
YEAR_COL_RANK = "{year}_직급"
```

---

## 시트별 구조 정의

### 직원정보 (헤더 2행 병합 구조)
- row[0]: 연도 행 (병합셀, forward fill로 처리)
- row[1]: 컬럼명 행
- 데이터: 3행부터
- 고정 컬럼: UserNo, 임직원명, PRS ID, 입사일자
- 연도별 컬럼: 부서명, 직위, 직급 (평탄화 후 "2026_부서명" 형태로 사용)
- 퇴사자 판별: CURRENT_YEAR 부서명이 빈칸이면 로드 시 제외

### login
- 헤더: 1행
- 주요 컬럼: UserNo, 이름, 부서, 직급, 로그인 일자
- 이메일 없음

### download
- 헤더: 1행
- 주요 컬럼: UserNo, 사용자ID(이메일), 다운로드 일자

### 제안서_ezPDF
- 헤더: 1행
- UserNo 없음, 유저ID(이메일) 있음

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
파일은 하나이며 외부에서는 load_all()과 run_all()만 호출.

### [load 블록]

**역할**
- Google Sheets 인증 및 연결
- 각 시트를 원본 그대로 DataFrame으로 반환
- 직원정보 헤더 평탄화: 2행 헤더를 "연도_컬럼명" 형태로 변환

**직원정보 헤더 평탄화 방식**
```
row[0] = ["", "", "", "2025", "2025", "2026", "2026", ...]
row[1] = ["No", "UserNo", "임직원명", "부서명", "직급", "부서명", "직급", ...]

결과 컬럼명 = ["No", "UserNo", "임직원명", "2025_부서명", "2025_직급", "2026_부서명", "2026_직급", ...]
```
- 연도 셀 빈칸은 직전 값 이어받기 (forward fill)
- 고정 컬럼(No, UserNo, 임직원명, PRS ID, 입사일자)은 prefix 없이 그대로 사용
- 2027년 컬럼이 시트에 추가되면 자동으로 "2027_부서명" 생성, 코드 수정 불필요

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

**연도별 마스터 분리**
```
각 로그 행의 year 컬럼을 기준으로
year=2025 -> df_users의 "2025_부서명", "2025_직급" 컬럼 참조
year=2026 -> df_users의 "2026_부서명", "2026_직급" 컬럼 참조
```
2025년 로그에는 2025년 소속 부서가, 2026년 로그에는 2026년 소속 부서가 붙음.

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
- year 컬럼 추가 (date에서 자동 추출, 신규 연도 데이터 쌓이면 자동 반영)
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
임원: 위 해당 없는 경우
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

## pages 공통 규칙

**공통 매개변수: 날짜**
모든 페이지는 날짜 필터를 기본으로 가짐.
날짜 필터 UI는 각 페이지 상단 또는 사이드바에 동일한 방식으로 배치.

```
날짜 빠른 선택: 오늘 / 최근 1주일 / 전체 / 직접 지정
```

**공통 규칙**
- session_state에서 DataFrame을 받아 필터 및 시각화만 수행
- merge, 매핑, 컬럼 처리 금지
- data.py의 st.* 호출 금지 (UI 의존성 차단)

---

## pages 구성 (1단계: 1_total.py만 구현, 나머지는 2단계)

### pages/1_total.py - Total Dashboard
기존 app.py UI를 이관. 전체 현황 요약.

현재 구현된 항목:
- D+카운터
- KPI (로그인수, 제안서 다운로드, 프로젝트/운영자료/서포트 건수)
- 일자별 활동 현황 (라인차트)
- 직원별 활동 로그 상세 테이블
- 제안서 과다 다운로더 모니터링

---

### pages/2_user.py - User (2단계)
사용자 단위 분석. 별도 spec 작성 예정.

---

### pages/3_department.py - Department & Team (2단계)
부서/팀 단위 분석. 연도 비교 포함. 별도 spec 작성 예정.
노드번호 기반 부서 연속성 추적은 추후 부서마스터 시트 추가 시 반영.

---

### pages/4_file.py - File (2단계)
파일/문서 단위 분석. 별도 spec 작성 예정.

---

### pages/5_kpi.py - Check KPI (2단계)
KPI 달성 현황. 별도 spec 작성 예정.

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
    v
app.py: st.session_state 저장
    |
    +-- pages/1_total.py      날짜 필터 -> 시각화
    +-- pages/2_user.py       날짜 필터 -> 사용자 분석
    +-- pages/3_department.py 날짜 필터 -> 부서 분석 + 연도 비교
    +-- pages/4_file.py       날짜 필터 -> 파일 분석
    +-- pages/5_kpi.py        날짜 필터 -> KPI 현황
```

---

## 예외 처리 기준

| 상황 | 처리 방법 |
|---|---|
| userNo 없는 행 (제안서 외) | 이름/부서/직급 빈값 유지, 행 삭제 금지 |
| 이메일 매핑 실패 (제안서) | 이름/부서/직급 빈값 유지, 행 삭제 금지 |
| 시트 없음 | 빈 DataFrame 반환 |
| 날짜 파싱 실패 | errors='coerce' 처리 (NaT) |
| 직원정보 중복 userNo | 첫 번째 행 사용 |
| 해당 연도 부서 컬럼 없음 | 빈값 유지 |

---

## 매년 유지보수 포인트

수정 위치는 config.py 한 곳.

```python
CURRENT_YEAR = 2027   # 변경
PREV_YEAR    = 2026   # 변경
BASE_DATE    = "2025-01-17"  # 변경 없음
```

직원정보 시트에 2027년 컬럼 추가 시 loader 자동 인식.
코드 수정 불필요.

---

## 금지 정책 요약

- userNo 임의 생성 금지
- 이름 기반 매핑/fallback 금지
- 원본 데이터 직접 수정 금지
- app.py, pages/*.py 에서 merge/매핑/컬럼 처리 금지
- data.py 에서 st.* 호출 금지
- config.py 외 파일에서 연도/날짜 하드코딩 금지

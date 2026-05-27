# EZ 데이터허브 로그 분석 대시보드 지표 정의서

## 1. 개요
본 문서는 EZ 데이터허브 로그 기반 대시보드에서 사용되는 주요 지표의 정의 및 계산 로직을 설명한다.  
모든 지표는 필터 조건(기간, 부서, 직급)에 의해 전처리된 데이터(`f_*`) 기준으로 산출된다.

---

## 2. 데이터 정의

| 데이터셋 | 설명 |
|----------|------|
| df_login | 로그인 로그 |
| df_download | 메뉴 접근 및 다운로드 로그 |
| df_proposal | 제안서 다운로드 로그 |
| df_users | 사용자 마스터 |

---

## 3. KPI 지표 정의 (상단)

### 3.1 총 로그인
- 정의: 선택 기간 내 로그인 발생 총 건수
- 계산식:
총 로그인 = len(f_login)
- 비고: 사용자 수가 아닌 이벤트 건수 기준

---

### 3.2 제안서 다운로드
- 정의: 제안서 다운로드 발생 건수
- 계산식:
제안서 DL = len(f_proposal)

---

### 3.3 프로젝트 찾기
- 정의: '프로젝트' 메뉴 접근 건수
프로젝트 찾기 = len(f_download[f_download['경로 메뉴명'].str.contains('프로젝트')])

---

### 3.4 운영자료 찾기
운영자료 찾기 = len(f_download[f_download['경로 메뉴명'].str.contains('운영자료')])

---

### 3.5 서포트 센터
서포트 센터 = len(f_download[f_download['경로 메뉴명'].str.contains('서포트')])

---

## 4. 추이 지표 (중단 좌측)

### 4.1 일자별 로그인 수
daily_login = f_login.groupby(date).size()

---

### 4.2 일자별 다운로드 수

제안서 다운로드:
dl_p = f_proposal.groupby(date).size()

주요 기능 사용 로그:
dl_d = f_download[
    f_download['경로 메뉴명'].str.contains('프로젝트|운영자료|서포트')
].groupby(date).size()

다운로드합계:
다운로드합계 = 제안서 + 사용로그

---

### 4.3 최종 추이 데이터
all_trends = 로그인수 + 다운로드합계 (날짜 기준 merge)

---

## 5. 이상 탐지 지표

### 제안서 다운로드 과다 사용자
heavy_users = f_proposal.groupby(['UserNo','이름','부서','직급']).size()
경고대상 = heavy_users[횟수 >= warning_threshold]

---

## 6. 사용자 기반 지표

### 전체 사용자 수
부서 기준:
total_users_dept = df_u.groupby('부서')['UserNo'].nunique()

직급 기준:
total_users_rank = df_u.groupby('직급그룹')['UserNo'].nunique()

---

### 활성 사용자 정의
active_users_all = concat(
    f_proposal[['UserNo']],
    f_download[조건]['UserNo']
).drop_duplicates()

---

### 사용률 계산
사용률 (%) = (순사용자 / 전체인원) * 100

---

## 7. 데이터 정합성 처리
'부서', '직급그룹' → '정보미등록'

---

## 8. 결론
사용자 활동, 조직별 활용도, 이상 행위를 분석하는 로그 기반 대시보드이다.

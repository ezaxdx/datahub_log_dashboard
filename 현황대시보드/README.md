# datahub_log_dashboard
[AXDX] 데이터허브 로그 대시보드 구축 프로젝트

- 프로젝트 기간: 2026-03 ~
- 배포: https://datalog-dashboard.streamlit.app

## 프로젝트 개요
사용자 행동 로그 기반 이상 탐지 및 실시간 모니터링 대시보드 구축

## 기술 스택
- Python, Pandas, gspread
- Streamlit, Plotly
- Google Sheets API
- GitHub, Streamlit Cloud

## 프로젝트 구조
```
Antigravity/
└── 현황대시보드/
    ├── app.py
    ├── requirements.txt
    └── .streamlit/
        └── secrets.toml
```

## 실행 방법
```bash
pip install -r requirements.txt
streamlit run 현황대시보드/app.py
```

## 프로젝트 목표
1. 실시간 모니터링이 가능한 데이터허브 대시보드 구현
2. 사용자 로그 데이터를 기반으로 비정상 열람 패턴(이상행위) 탐지 기준 정의
3. 짧은 시간 내 다량 열람 등 위험행동을 정량적으로 식별
4. 운영자가 즉시 대응할 수 있도록 탐지 로직 구성

## 문제 정의
1. 각기 다른 페이지에 로그 적재 중 및 폐쇄 API 사용
2. 특정 사용자가 짧은 시간 내 다수의 제안서 반복 열람
3. 정상 사용자와 비정상 사용자의 행동 패턴 구분 어려움

## 분석 접근 방법
1. API 기반 로그인/열람 로그 수집
2. Google Sheets 및 JSON 형태로 데이터 적재
3. 로그 누적을 고려한 증분 적재 구조 설계 (checkpoint 활용)

## 핵심 지표
1. 사용자별 열람 횟수
2. 동일 프로젝트 내 열람 빈도
3. 열람 간 시간 간격
4. 특정 시간 내 열람 집중도

## 이상 탐지 로직
1. 일정 시간 내 열람 횟수 임계치 초과
2. 동일 콘텐츠 반복 접근 패턴 감지

## 대시보드 구현
1. 기간별 사용자 현황 파악
2. 사용자별 열람 패턴 시각화
3. 프로젝트별 접근 현황

## 향후 개선 방향
1. 실시간 스트리밍 데이터 처리 구조 도입
2. 알림 시스템 연동

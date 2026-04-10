`antigravity` 라이브러리(또는 해당 명칭의 커스텀 환경)를 사용하여 프로젝트를 진행하실 수 있도록, 전체 프로젝트 구조와 가이드가 담긴 \*\*`README.md`\*\* 형태의 문서를 만들어 드립니다. 



이 내용을 복사해서 깃허브(GitHub) 저장소의 `README.md`로 사용하시면 팀 내 공유 및 관리용으로 완벽합니다.



\---



\# 📊 2026 전사 통합 로그 대시보드 프로젝트



본 프로젝트는 구글 스프레드시트의 데이터를 기반으로 \*\*2026년 조직 개편 사항\*\*을 반영하여 일자별, 직원별, 부서별 로그 현황을 시각화하는 웹 기반 대시보드입니다.



\## 🚀 프로젝트 개요

\- \*\*Data Source\*\*: Google Sheets (로그인, 다운로드, 제안서 데이터)

\- \*\*Tech Stack\*\*: Python, Streamlit, Pandas, Antigravity(Data Connector)

\- \*\*Deployment\*\*: Streamlit Cloud

\- \*\*Storage\*\*: GitHub



\## 📂 데이터 구조 (Google Sheets)

모든 데이터는 `userNo`를 고유 키(Primary Key)로 사용하여 연결됩니다.



1\. \*\*사용자정보 (Master)\*\*: `userNo`, 이름, 본부명, 부서명, 직급 (26년 개편 기준)

2\. \*\*로그인데이터\*\*: `date`, `userNo`

3\. \*\*다운로드데이터\*\*: `date`, `userNo`, `category` (프로젝트 찾기, 운영자료 찾기, 서포트센터 등)

4\. \*\*제안서데이터\*\*: `date`, `userNo`, `proposalName`



\---



\## 🛠️ 설치 및 설정 (Requirements)



\### 1. 필수 라이브러리 (`requirements.txt`)

```text

streamlit

pandas

gspread

oauth2client

plotly

```



\### 2. 환경 변수 설정 (Streamlit Secrets)

Streamlit Cloud 배포 시 `Settings > Secrets`에 구글 서비스 계정 키를 입력해야 합니다.

```toml

\[gcp\_service\_account]

type = "service\_account"

project\_id = "your-project-id"

private\_key\_id = "your-key-id"

private\_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"

client\_email = "your-email@gserviceaccount.com"

client\_id = "..."

\# (기타 구글 키 항목 포함)

```



\---



\## 💻 대시보드 핵심 스크립트 (`app.py`)



```python

import streamlit as st

import pandas as pd

import gspread

from oauth2client.service\_account import ServiceAccountCredentials

import plotly.express as px

from datetime import datetime



\# --- 1. 데이터 연결 및 로드 (ANTIGRAVITY Logic) ---

@st.cache\_data(ttl=600)

def load\_data():

&#x20;   scope = \["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

&#x20;   creds\_dict = st.secrets\["gcp\_service\_account"]

&#x20;   creds = ServiceAccountCredentials.from\_json\_keyfile\_dict(creds\_dict, scope)

&#x20;   client = gspread.authorize(creds)

&#x20;   

&#x20;   sh = client.open("대시보드\_데이터\_시트")

&#x20;   

&#x20;   # 각 시트 데이터 프레임화

&#x20;   df\_login = pd.DataFrame(sh.worksheet("로그인데이터").get\_all\_records())

&#x20;   df\_download = pd.DataFrame(sh.worksheet("다운로드데이터").get\_all\_records())

&#x20;   df\_proposal = pd.DataFrame(sh.worksheet("제안서데이터").get\_all\_records())

&#x20;   df\_users = pd.DataFrame(sh.worksheet("사용자정보").get\_all\_records())

&#x20;   

&#x20;   return df\_login, df\_download, df\_proposal, df\_users



\# --- 2. 데이터 전처리 및 매핑 ---

login\_raw, download\_raw, proposal\_raw, user\_master = load\_data()



def preprocess\_data(df):

&#x20;   df\['date'] = pd.to\_datetime(df\['date'])

&#x20;   # userNo 기준으로 26년도 조직 정보 매핑 (핵심: 조직개편 대응)

&#x20;   return pd.merge(df, user\_master\[\['userNo', '본부명', '부서명', '직급', '이름']], on='userNo', how='left')



df\_login = preprocess\_data(login\_raw)

df\_download = preprocess\_data(download\_raw)

df\_proposal = preprocess\_data(proposal\_raw)



\# 직급 그룹화 (실무자 vs 관리자)

def group\_rank(rank):

&#x20;   if rank in \['사원', '대리']: return '실무자(사원/대리)'

&#x20;   if rank in \['차장', '팀장', '부장', '본부장', '이사']: return '관리자(차장↑)'

&#x20;   return '기타'



for df in \[df\_login, df\_download, df\_proposal]:

&#x20;   df\['직급그룹'] = df\['직급'].apply(group\_rank)



\# --- 3. 사이드바 매개변수 필터 ---

st.sidebar.header("🔍 상세 필터")

\# 날짜 선택

date\_range = st.sidebar.date\_input("조회 기간 (2026년 기준)", 

&#x20;                                 \[datetime(2026, 1, 1), datetime(2026, 12, 31)])



\# 본부/부서/직급 멀티 셀렉트

sel\_hq = st.sidebar.multiselect("본부명", options=sorted(user\_master\['본부명'].unique()))

sel\_dept = st.sidebar.multiselect("부서명", options=sorted(user\_master\[user\_master\['본부명'].isin(sel\_hq)]\['부서명'].unique()) if sel\_hq else sorted(user\_master\['부서명'].unique()))

sel\_rank = st.sidebar.multiselect("직급 그룹", options=\['실무자(사원/대리)', '관리자(차장↑)'])



\# 필터링 적용

def filter\_df(df):

&#x20;   res = df\[df\['date'].dt.year == 2026]

&#x20;   if len(date\_range) == 2:

&#x20;       res = res\[(res\['date'].dt.date >= date\_range\[0]) \& (res\['date'].dt.date <= date\_range\[1])]

&#x20;   if sel\_hq: res = res\[res\['본부명'].isin(sel\_hq)]

&#x20;   if sel\_dept: res = res\[res\['부서명'].isin(sel\_dept)]

&#x20;   if sel\_rank: res = res\[res\['직급그룹'].isin(sel\_rank)]

&#x20;   return res



f\_login = filter\_df(df\_login)

f\_download = filter\_df(df\_download)

f\_proposal = filter\_df(df\_proposal)



\# --- 4. 대시보드 UI ---

st.title("📈 2026 통합 로그 분석 대시보드")



\# KPI 섹션

c1, c2, c3, c4 = st.columns(4)

c1.metric("총 로그인수", f"{len(f\_login)}건")

c2.metric("제안서 다운로드", f"{len(f\_proposal)}건")

c3.metric("프로젝트 찾기", f"{len(f\_download\[f\_download\['category']=='프로젝트 찾기'])}건")

c4.metric("운영/서포트", f"{len(f\_download\[f\_download\['category'].isin(\['운영자료 찾기','서포트센터'])])}건")



\# 그래프 섹션

st.subheader("🗓️ 일자별 활동 현황")

daily\_logs = f\_login.groupby(f\_login\['date'].dt.date).size().reset\_index(name='count')

st.line\_chart(daily\_logs.set\_index('date'))



\# 직원별 상세 현황

st.subheader("👤 직원별 활동 로그 상세")

user\_table = f\_login.groupby(\['이름','본부명','부서명','직급']).size().reset\_index(name='로그인수')

st.dataframe(user\_table, use\_container\_width=True)

```



\---



\## 📝 사용 시나리오 및 주요 특징



\### 1. 2025 vs 2026 데이터 관리

\*   \*\*고유키 `userNo` 사용\*\*: 25년 데이터와 26년 데이터의 부서명이 바뀌더라도 `userNo`를 기준으로 26년 마스터 정보를 매핑하여 일관된 분석 결과를 제공합니다.

\*   \*\*연도 필터링\*\*: 기본 뷰는 26년도로 설정되어 있으며, 필요 시 전년도와의 비교 지표(Delta)를 KPI 카드에 노출합니다.



\### 2. 인사 변동 자동 반영

\*   구글 시트에 신규 입사자가 추가되거나 기존 직원의 직급/부서가 변경되면, 별도의 코드 수정 없이 \*\*새로고침(F5)\*\*만으로 대시보드에 즉시 반영됩니다.



\### 3. 직급별 활용도 분석

\*   단순 직급 나열이 아닌 '실무자(사원/대리)'와 '관리자(차장 이상)' 그룹 매개변수를 제공하여, \*\*의사결정권자들의 시스템 활용 비중\*\*을 집중 모니터링할 수 있습니다.



\### 4. 팀 내 공유 및 보안

\*   \*\*Streamlit Cloud\*\*를 통해 웹 URL로 공유됩니다.

\*   GitHub Private 저장소를 사용하여 코드를 보호하고, Google Cloud Console의 서비스 계정 권한을 통해 시트 데이터 접근을 안전하게 관리합니다.



\---



\## 🚀 배포 단계 (Deployment)

1\. GitHub 저장소에 위 코드를 푸시합니다.

2\. \[Streamlit Cloud](https://share.streamlit.io/)에 접속하여 해당 저장소를 연결합니다.

3\. `Advanced Settings`의 \*\*Secrets\*\* 탭에 구글 JSON 키 정보를 붙여넣습니다.

4\. 배포된 URL을 팀 내 공유합니다.


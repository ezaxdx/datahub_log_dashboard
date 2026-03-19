import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime

# --- 1. 데이터 연결 및 로드 (ANTIGRAVITY Logic) ---
@st.cache_data(ttl=600)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    sh = client.open("대시보드_데이터_시트")
    
    # 각 시트 데이터 프레임화
    df_login = pd.DataFrame(sh.worksheet("로그인데이터").get_all_records())
    df_download = pd.DataFrame(sh.worksheet("다운로드데이터").get_all_records())
    df_proposal = pd.DataFrame(sh.worksheet("제안서데이터").get_all_records())
    df_users = pd.DataFrame(sh.worksheet("사용자정보").get_all_records())
    
    return df_login, df_download, df_proposal, df_users

# --- 2. 데이터 전처리 및 매핑 ---
login_raw, download_raw, proposal_raw, user_master = load_data()

def preprocess_data(df):
    df['date'] = pd.to_datetime(df['date'])
    # userNo 기준으로 26년도 조직 정보 매핑 (핵심: 조직개편 대응)
    return pd.merge(df, user_master[['userNo', '본부명', '부서명', '직급', '이름']], on='userNo', how='left')

df_login = preprocess_data(login_raw)
df_download = preprocess_data(download_raw)
df_proposal = preprocess_data(proposal_raw)

# 직급 그룹화 (실무자 vs 관리자)
def group_rank(rank):
    if rank in ['사원', '대리']: return '실무자(사원/대리)'
    if rank in ['차장', '팀장', '부장', '본부장', '이사']: return '관리자(차장↑)'
    return '기타'

for df in [df_login, df_download, df_proposal]:
    df['직급그룹'] = df['직급'].apply(group_rank)

# --- 3. 사이드바 매개변수 필터 ---
st.sidebar.header("🔍 상세 필터")
# 날짜 선택
date_range = st.sidebar.date_input("조회 기간 (2026년 기준)", 
                                  [datetime(2026, 1, 1), datetime(2026, 12, 31)])

# 본부/부서/직급 멀티 셀렉트
sel_hq = st.sidebar.multiselect("본부명", options=sorted(user_master['본부명'].unique()))
sel_dept = st.sidebar.multiselect("부서명", options=sorted(user_master[user_master['본부명'].isin(sel_hq)]['부서명'].unique()) if sel_hq else sorted(user_master['부서명'].unique()))
sel_rank = st.sidebar.multiselect("직급 그룹", options=['실무자(사원/대리)', '관리자(차장↑)'])

# 필터링 적용
def filter_df(df):
    res = df[df['date'].dt.year == 2026]
    if len(date_range) == 2:
        res = res[(res['date'].dt.date >= date_range[0]) & (res['date'].dt.date <= date_range[1])]
    if sel_hq: res = res[res['본부명'].isin(sel_hq)]
    if sel_dept: res = res[res['부서명'].isin(sel_dept)]
    if sel_rank: res = res[res['직급그룹'].isin(sel_rank)]
    return res

f_login = filter_df(df_login)
f_download = filter_df(df_download)
f_proposal = filter_df(df_proposal)

# --- 4. 대시보드 UI ---
st.title("📈 2026 통합 로그 분석 대시보드")

# KPI 섹션
c1, c2, c3, c4 = st.columns(4)
c1.metric("총 로그인수", f"{len(f_login)}건")
c2.metric("제안서 다운로드", f"{len(f_proposal)}건")
c3.metric("프로젝트 찾기", f"{len(f_download[f_download['category']=='프로젝트 찾기'])}건")
c4.metric("운영/서포트", f"{len(f_download[f_download['category'].isin(['운영자료 찾기','서포트센터'])])}건")

# 그래프 섹션
st.subheader("🗓️ 일자별 활동 현황")
daily_logs = f_login.groupby(f_login['date'].dt.date).size().reset_index(name='count')
st.line_chart(daily_logs.set_index('date'))

# 직원별 상세 현황
st.subheader("👤 직원별 활동 로그 상세")
user_table = f_login.groupby(['이름','본부명','부서명','직급']).size().reset_index(name='로그인수')
st.dataframe(user_table, use_container_width=True)

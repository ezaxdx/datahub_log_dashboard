import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config

# --- [UI Style Helper: Metrics] ---
def render_metric_card(label, value, color="#6366f1"):
    st.markdown(f"""
    <div class="metric-card" style="text-align: center; border-left: 4px solid {color}; padding-left: 10px;">
        <div style="color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase;">{label}</div>
        <div style="color: #1e293b; font-size: 20px; font-weight: 800;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- [Page Header: Original] ---
st.markdown(f"""
<div class="page-header" style="padding: 12px 24px; margin-bottom: 16px;">
    <div style="font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; opacity: 0.8;">Overview</div>
    <div style="font-size: 24px; font-weight: 800; margin-bottom: 4px;"> {config.CURRENT_YEAR} EZ데이터허브 로그 분석 대시보드</div>
    <div style="font-size: 13px; opacity: 0.85; font-weight: 400;"> 사용자의 전반적인 사용량 및 활동 현황을 모니터링합니다. </div>
</div>
""", unsafe_allow_html=True)

# --- 1. 데이터 가져오기 ---
df_u = st.session_state.get('df_users', pd.DataFrame())
df_login = st.session_state.get('df_login', pd.DataFrame())
df_download = st.session_state.get('df_download', pd.DataFrame())
df_proposal = st.session_state.get('df_proposal', pd.DataFrame())

# --- 2. 필터 값 가져오기 ---
date_preset = st.session_state.get('date_preset', '전체')
date_range = st.session_state.get('date_range', None)
sel_dept = st.session_state.get('sel_dept', [])
sel_rank = st.session_state.get('sel_rank', [])
warning_threshold = st.session_state.get('warning_threshold', 10)

# --- 3. 데이터 필터링 함수 ---
def filter_data(df):
    if df.empty: return df
    res = df.copy()
    if 'date' in res.columns:
        if date_preset == "오늘":
            res = res[res['date'].dt.date == datetime.now().date()]
        elif date_preset == "최근 1주일":
            start_date = datetime.now().date() - timedelta(days=7)
            res = res[(res['date'].dt.date >= start_date) & (res['date'].dt.date <= datetime.now().date())]
        elif date_preset == "직접 지정" and date_range:
            if len(date_range) == 2:
                res = res[(res['date'].dt.date >= date_range[0]) & (res['date'].dt.date <= date_range[1])]
    if sel_dept and '부서' in res.columns:
        res = res[res['부서'].isin(sel_dept)]
    elif sel_dept and '부서' in res.columns: # df_users용
        res = res[res['부서'].isin(sel_dept)]
    
    if sel_rank and '직급그룹' in res.columns:
        res = res[res['직급그룹'].isin(sel_rank)]
    return res

f_login = filter_data(df_login)
f_download = filter_data(df_download)
f_proposal = filter_data(df_proposal)
f_u = filter_data(df_u)

# [수치 정합성] 부서/직급 정보가 없는 데이터를 '정보미등록'으로 채움
for df in [f_login, f_download, f_proposal, f_u]:
    if not df.empty:
        # data.py에서 제공하는 표준 컬럼 사용 및 결측치 최종 보정
        if '부서' in df.columns: 
            df['부서'] = df['부서'].replace(['', None, 'nan', 'NaN'], '정보미등록').fillna('정보미등록')
        if '직급그룹' in df.columns: 
            df['직급그룹'] = df['직급그룹'].replace(['', None, 'nan', 'NaN'], '정보미등록').fillna('정보미등록')

def get_menu_count(df, pattern):
    if df.empty or '경로 메뉴명' not in df.columns: return 0
    return len(df[df['경로 메뉴명'].astype(str).str.contains(pattern, na=False)])

# --- 4. 상단 KPI 섹션 ---
kpi_cols = st.columns(5)
with kpi_cols[0]: render_metric_card("총 로그인", f"{len(f_login):,}건", "#6366f1")
with kpi_cols[1]: render_metric_card("제안서 DL", f"{len(f_proposal):,}건", "#f59e0b")
with kpi_cols[2]: render_metric_card("프로젝트 찾기", f"{get_menu_count(f_download, '프로젝트'):,}건", "#10b981")
with kpi_cols[3]: render_metric_card("운영자료 찾기", f"{get_menu_count(f_download, '운영자료'):,}건", "#3b82f6")
with kpi_cols[4]: render_metric_card("서포트 센터", f"{get_menu_count(f_download, '서포트'):,}건", "#ec4899")

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# --- 5. 중단 1행 (추이 및 경고) ---
col_mid_left, col_mid_right = st.columns([2, 1])

with col_mid_left:
    st.markdown("##### 📈 일자별 활동 현황")
    if not f_login.empty and 'date' in f_login.columns:
        daily_login = f_login.groupby(f_login['date'].dt.date).size().reset_index(name='로그인수')
        dl_p = f_proposal.groupby(f_proposal['date'].dt.date).size().reset_index(name='제안서')
        dl_d = f_download[f_download['경로 메뉴명'].astype(str).str.contains('프로젝트|운영자료|서포트', na=False)]
        dl_d = dl_d.groupby(dl_d['date'].dt.date).size().reset_index(name='사용로그')
        merged_dl = pd.merge(dl_p, dl_d, on='date', how='outer').fillna(0)
        merged_dl['다운로드합계'] = merged_dl['제안서'] + merged_dl['사용로그']
        all_trends = pd.merge(daily_login, merged_dl[['date', '다운로드합계']], on='date', how='outer').fillna(0).sort_values('date')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=all_trends['date'], y=all_trends['로그인수'], name='로그인수', line=dict(color='#6366f1', width=3)))
        fig.add_trace(go.Scatter(x=all_trends['date'], y=all_trends['다운로드합계'], name='다운로드합계', line=dict(color='#10b981', width=3), yaxis='y2'))
        fig.update_layout(
            height=220, margin=dict(l=40, r=40, t=10, b=40),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
            yaxis=dict(title=dict(text="로그인 수", font=dict(size=10, color="#6366f1")), tickfont=dict(size=10, color="#6366f1")),
            yaxis2=dict(title=dict(text="다운로드 수", font=dict(size=10, color="#10b981")), tickfont=dict(size=10, color="#10b981"), anchor="x", overlaying="y", side="right")
        )
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("데이터 없음")

with col_mid_right:
    st.markdown("##### ⚠️ 제안서 다운로드 경고 직원")
    if not f_proposal.empty:
        agg_cols = ['UserNo', '이름', '부서', '직급']
        heavy_users = f_proposal.groupby(agg_cols).size().reset_index(name='횟수')
        heavy_users = heavy_users[heavy_users['횟수'] >= warning_threshold].sort_values(by='횟수', ascending=False)
        if not heavy_users.empty:
            st.dataframe(heavy_users, use_container_width=True, hide_index=True, height=180)
        else: st.success("경고 대상 없음")
    else: st.info("데이터 없음")

# --- 6. 하단 2행 (부서/직급별 사용량 및 사용률 분석 - TOP5 표 교체) ---
st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

# 데이터 준비 (분모를 f_u 기준으로 통일)
active_p = f_proposal[['UserNo', '부서', '사업부', '직급']]
active_d = f_download[f_download['경로 메뉴명'].astype(str).str.contains('프로젝트|운영자료|서포트', na=False)][['UserNo', '부서', '사업부', '직급']]
active_users_all = pd.concat([active_p, active_d]).drop_duplicates(subset=['UserNo'])

# 1. 부서별 로그인 TOP5
login_dept_top5 = (
    f_login.groupby('부서').size()
    .reset_index(name='로그인수')
    .sort_values('로그인수', ascending=False)
    .head(5)
    .reset_index(drop=True)
)

# 2. 사업부별 사용률 TOP5 (변경: 부서 -> 사업부)
active_by_div = active_users_all.groupby('사업부')['UserNo'].nunique().reset_index(name='순사용자')
total_users_div = f_u.groupby('사업부')['UserNo'].nunique().reset_index(name='전체인원')
usage_div = pd.merge(total_users_div, active_by_div, on='사업부', how='left').fillna(0)
usage_div['사용률(%)'] = (usage_div['순사용자'] / usage_div['전체인원'] * 100).round(1)
usage_div_top5 = (
    usage_div[['사업부', '전체인원', '순사용자', '사용률(%)']]
    .sort_values('사용률(%)', ascending=False)
    .head(5)
    .reset_index(drop=True)
)

# 3. 직급별 로그인 현황
login_rank_all = (
    f_login.groupby('직급').size()
    .reset_index(name='로그인수')
    .sort_values('로그인수', ascending=False)
    .reset_index(drop=True)
)

# 4. 직급별 사용률 현황
active_by_rank = active_users_all.groupby('직급')['UserNo'].nunique().reset_index(name='순사용자')
total_users_rank = f_u.groupby('직급')['UserNo'].nunique().reset_index(name='전체인원')
usage_rank = pd.merge(total_users_rank, active_by_rank, on='직급', how='left').fillna(0)
usage_rank['사용률(%)'] = (usage_rank['순사용자'] / usage_rank['전체인원'] * 100).round(1)
usage_rank_all = (
    usage_rank[['직급', '전체인원', '순사용자', '사용률(%)']]
    .sort_values('사용률(%)', ascending=False)
    .reset_index(drop=True)
)

# 레이아웃 배치 (1행 4열 표 교체)
col_t1, col_t2, col_t3, col_t4 = st.columns(4)
table_height = 210

with col_t1:
    st.markdown("##### 부서별 로그인 TOP5")
    st.dataframe(login_dept_top5, use_container_width=True, hide_index=True, height=table_height)

with col_t2:
    st.markdown("##### 사업부별 사용률 TOP5")
    st.dataframe(usage_div_top5, use_container_width=True, hide_index=True, height=table_height)

with col_t3:
    st.markdown("##### 직급별 로그인 현황")
    st.dataframe(login_rank_all, use_container_width=True, hide_index=True, height=table_height)

with col_t4:
    st.markdown("##### 직급별 사용률 현황")
    st.dataframe(usage_rank_all, use_container_width=True, hide_index=True, height=table_height)
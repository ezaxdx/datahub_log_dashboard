import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config

# --- [UI Style Helper: Metrics] ---
def render_metric_card(label, value, color="#6366f1"):
    st.markdown(f"""
    <div class="metric-card" style="text-align: center; border-left: 4px solid {color}; padding-left: 10px; background: #f8fafc; padding: 15px; border-radius: 8px;">
        <div style="color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 5px;">{label}</div>
        <div style="color: #1e293b; font-size: 22px; font-weight: 800;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- [Page Header] ---
st.markdown(f"""
<div class="page-header" style="padding: 12px 24px; margin-bottom: 16px;">
    <div style="font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; opacity: 0.8;">Analytics</div>
    <div style="font-size: 24px; font-weight: 800; margin-bottom: 4px;"> 2026 EZ데이터허브 KPI (목표 달성 현황)</div>
    <div style="font-size: 13px; opacity: 0.85; font-weight: 400;"> 목표 대비 핵심 성과 지표(KPI) 달성 여부를 모니터링합니다. </div>
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

# --- 3. 공통 필터링 함수 (1_total.py 기반) ---
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
                # 시작일과 종료일이 모두 선택된 경우
                res = res[(res['date'].dt.date >= date_range[0]) & (res['date'].dt.date <= date_range[1])]
            elif len(date_range) == 1:
                # 시작일만 선택된 경우, 해당 날짜 이후의 모든 데이터 표시
                res = res[res['date'].dt.date >= date_range[0]]
    
    if sel_dept and '부서' in res.columns:
        res = res[res['부서'].isin(sel_dept)]
    if sel_rank and '직급그룹' in res.columns:
        res = res[res['직급그룹'].isin(sel_rank)]
    return res

f_login = filter_data(df_login)
f_download = filter_data(df_download)
f_proposal = filter_data(df_proposal)

# [KPI 전용] 2026년도 확대 적용일(4월 10일) 필터링 함수
def apply_kpi_temporal_logic(df):
    if df.empty or 'date' not in df.columns: return df
    # 2026년 데이터가 포함되어 있는지 확인
    years_in_data = df['date'].dt.year.unique()
    if 2026 in years_in_data:
        # 2026년 데이터에 대해서만 4월 10일 이후로 제한
        # (단, 사용자가 2027년 등을 선택했다면 그 연도는 통째로 나옴)
        # 여기서는 "선택한 연도가 2026년이고 4월 이전 데이터가 포함되었다면" 조건 충족을 위해
        # 2026년 데이터 중 4월 10일 이전 데이터를 제거함
        is_2026 = df['date'].dt.year == 2026
        is_pre_expansion = df['date'] < datetime(2026, 4, 10)
        df = df[~(is_2026 & is_pre_expansion)]
    return df

k_login = apply_kpi_temporal_logic(f_login)
k_download = apply_kpi_temporal_logic(f_download)
k_proposal = apply_kpi_temporal_logic(f_proposal)

# --- 4. 데이터 계산 ---
# 카테고리별 건수 추출
cnt_proposal = len(k_proposal)
cnt_project = len(k_download[k_download['경로 메뉴명'].astype(str).str.contains('프로젝트', na=False)])
cnt_ops = len(k_download[k_download['경로 메뉴명'].astype(str).str.contains('운영자료', na=False)])
cnt_support = len(k_download[k_download['경로 메뉴명'].astype(str).str.contains('서포트', na=False)])
cnt_total_dl = cnt_proposal + cnt_project + cnt_ops + cnt_support

# 순 사용자 (Active Users): 로그인/다운로드 기록이 있는 유니크 유저
active_users_list = pd.concat([
    k_login['UserNo'] if not k_login.empty else pd.Series(),
    k_download['UserNo'] if not k_download.empty else pd.Series(),
    k_proposal['UserNo'] if not k_proposal.empty else pd.Series()
]).unique()
cnt_active_users = len(active_users_list) if len(active_users_list) > 0 else 1 # 0나누기 방지

# 인당 평균 총 다운로드 수
avg_dl_per_person = cnt_total_dl / cnt_active_users

# KPI 목표 달성률 (목표 56회)
target_value = 56
kpi_attainment = (avg_dl_per_person / target_value) * 100

# --- 5. 상단 KPI 카드 ---
kpi_cols = st.columns(4)
with kpi_cols[0]: 
    render_metric_card("인당 평균 총 다운로드", f"{avg_dl_per_person:.1f}회", "#6366f1")
with kpi_cols[1]: 
    render_metric_card("순 사용자 (Active)", f"{len(active_users_list):,}명", "#10b981")
with kpi_cols[2]: 
    render_metric_card("총 다운로드 수", f"{cnt_total_dl:,}건", "#3b82f6")
with kpi_cols[3]: 
    # 목표 달성률 색상 분기
    attainment_color = "#10b981" if kpi_attainment >= 100 else "#f59e0b"
    render_metric_card("KPI 목표 달성률", f"{kpi_attainment:.1f}%", attainment_color)

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# --- 6. 하단 2열 레이아웃 (1:2 비중) ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("##### 📊 카테고리별 사용 비중")
    # 차트 데이터 구성
    ratio_df = pd.DataFrame({
        "구분": ["전체 비중"] * 4,
        "항목": ["제안서", "프로젝트", "운영자료", "서포트"],
        "건수": [cnt_proposal, cnt_project, cnt_ops, cnt_support]
    })
    total_for_ratio = ratio_df["건수"].sum()
    ratio_df["비중(%)"] = (ratio_df["건수"] / total_for_ratio * 100).round(1) if total_for_ratio > 0 else 0
    
    # 색상 맵핑 정의 (기존 대시보드와 통일)
    color_map = {
        "제안서": "#f59e0b",   # Amber
        "프로젝트": "#10b981", # Emerald
        "운영자료": "#3b82f6", # Blue
        "서포트": "#ec4899"    # Pink
    }

    # 세로 누적 막대 그래프
    fig_bar = px.bar(
        ratio_df, x="구분", y="비중(%)", color="항목",
        text="비중(%)", 
        color_discrete_map=color_map,
        custom_data=["건수"]
    )
    fig_bar.update_traces(
        texttemplate='%{text}%', textposition='inside',
        hovertemplate="<b>%{customdata[1]}</b><br>비중: %{y}%<br>총 %{customdata[0]}건<extra></extra>"
    )
    # custom_data에 항목명도 넣기 위해 수정
    fig_bar.update_traces(customdata=ratio_df[["건수", "항목"]].values)

    fig_bar.update_layout(
        height=350, margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="", yaxis_title="비중 (%)",
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        barmode='stack'
    )
    # X축 라벨 제거 (깔끔하게)
    fig_bar.update_xaxes(showticklabels=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col_right:
    st.markdown("##### 📈 월별 순 로그인 및 누계")
    
    # 월별 데이터 집계 (1-12월 고정)
    months = list(range(1, 13))
    login_monthly = []
    
    # 현재 조회 데이터의 연도 파악
    view_year = config.CURRENT_YEAR
    if not f_login.empty:
        view_year = f_login['date'].dt.year.iloc[0]
    elif not f_proposal.empty:
        view_year = f_proposal['date'].dt.year.iloc[0]
        
    for m in months:
        # 월별 필터링
        m_df = f_login[f_login['date'].dt.month == m]
        
        # 2026년 특수 로직
        if view_year == 2026:
            if m < 4:
                login_monthly.append(0)
            elif m == 4:
                # 4월 10일 이후만
                m_df_4 = m_df[m_df['date'] >= datetime(2026, 4, 10)]
                login_monthly.append(m_df_4['UserNo'].nunique())
            else:
                login_monthly.append(m_df['UserNo'].nunique())
        else:
            # 2026년이 아니면 전체 집계
            login_monthly.append(m_df['UserNo'].nunique())
            
    # 누계 계산
    login_cumsum = []
    current_sum = 0
    for val in login_monthly:
        current_sum += val
        login_cumsum.append(current_sum)
        
    # 이중 축 그래프 생성
    fig_line = go.Figure()
    # Line 1: 월별 순 로그인
    fig_line.add_trace(go.Bar(
        x=[f"{m}월" for m in months], y=login_monthly, 
        name="순 로그인 수", marker_color="#6366f1", opacity=0.7
    ))
    # Line 2: 누계
    fig_line.add_trace(go.Scatter(
        x=[f"{m}월" for m in months], y=login_cumsum, 
        name="로그인 누계", line=dict(color="#f43f5e", width=3),
        yaxis="y2"
    ))
    
    fig_line.update_layout(
        height=350, margin=dict(l=20, r=40, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            title=dict(text="순 로그인 수", font=dict(color="#6366f1")), 
            tickfont=dict(color="#6366f1")
        ),
        yaxis2=dict(
            title=dict(text="누계", font=dict(color="#f43f5e")), 
            tickfont=dict(color="#f43f5e"), 
            overlaying="y", side="right"
        ),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_line, use_container_width=True)

# 하단 정보 안내
st.info(f"""
💡 **KPI 기준 안내**
- **목표치:** 2026년 인당 평균 총 다운로드 수 {target_value}회 이상 (연간 환산 기준)
- **적용 로직:** 2026년 데이터의 경우 전사 확대 시점인 **4월 10일** 이후 데이터만 KPI 지표에 산입됩니다. (내년부터는 1월부터 자동 산입)
""")

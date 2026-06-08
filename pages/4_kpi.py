import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config

# --- [UI Style Helper: Metrics] ---
def render_metric_card(label, value, delta=None, desc=None):
    delta_html = ""
    if delta:
        d_val, d_color = delta
        delta_html = f'<div style="font-size: 11px; font-weight: 700; color: {d_color};">{d_val}</div>'
    desc_html = f'<div style="font-size: 11px; color: #94a3b8; margin-top: 6px; font-family: \'Inter\';">{desc}</div>' if desc else ""
    html = f'<div class="metric-card"><div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;"><div style="color: #64748b; font-size: 13px; font-weight: 700; text-transform: uppercase; font-family: \'Inter\';">{label}</div>{delta_html}</div><div style="color: #1e293b; font-size: 28px; font-weight: 800; font-family: \'Manrope\';">{value}</div>{desc_html}</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- [Page Header] ---
st.markdown(f"""
<div class="page-header">
    <div style="font-size: 10px; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-family: 'Inter';">Strategic Analytics</div>
    <div style="font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 4px; font-family: 'Manrope';">2026 EZ데이터허브 KPI 달성 현황</div>
    <div style="font-size: 14px; color: #64748b; font-weight: 400; font-family: 'Inter';">
        {config.CURRENT_YEAR}년 1월~현재 월 누적 기준 · 임직원 인당 평균 다운로드 수 달성 여부를 모니터링합니다.<br>
        <span style="font-size: 12px; color: #94a3b8;">※ KPI 수치는 사이드바 필터와 무관하게 전사 기준으로 고정 집계됩니다.</span>
    </div>
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

# [KPI 전용] 사이드바 필터 독립 — 현재연도 1월~현재월 고정 집계
# 날짜/부서/직급 사이드바 필터를 무시하고, 원본 데이터 기준 전사 집계
_kpi_year  = config.CURRENT_YEAR
_kpi_month = datetime.now().month

# KPI 집계 제외 부서: AXDX팀(내부 운영팀) + MICE혁신본부(AXDX팀 본부장)
_KPI_EXCLUDE_DEPTS = {'AXDX팀', 'MICE혁신본부'}

def kpi_filter(df):
    """KPI 전용: 현재연도 1월 ~ 현재 월까지 고정, 사이드바 필터 미적용, AXDX팀 제외"""
    if df.empty or 'date' not in df.columns:
        return df
    mask = (df['date'].dt.year == _kpi_year) & (df['date'].dt.month <= _kpi_month)
    res = df[mask].copy()
    # AXDX팀(내부 운영팀) 제외 — KPI는 전사 구성원 기준으로 집계
    if '부서' in res.columns:
        res = res[~res['부서'].isin(_KPI_EXCLUDE_DEPTS)]
    return res

k_download = kpi_filter(df_download)   # 원본 df — 사이드바 필터 무시
k_proposal = kpi_filter(df_proposal)
k_login    = kpi_filter(df_login)

# --- 4. 데이터 계산 ---
# 카테고리별 건수 추출 (프로젝트 찾기 / 프로젝트 실적 분리)
cnt_proposal    = len(k_proposal)
cnt_project     = len(k_download[k_download['경로 메뉴명'].astype(str).str.contains('프로젝트 찾기', na=False)])
cnt_performance = len(k_download[k_download['경로 메뉴명'].astype(str).str.contains('프로젝트 실적', na=False)])
cnt_ops         = len(k_download[k_download['경로 메뉴명'].astype(str).str.contains('운영자료', na=False)])
cnt_support     = len(k_download[k_download['경로 메뉴명'].astype(str).str.contains('서포트', na=False)])

# 총 다운로드 수
cnt_total_dl = cnt_proposal + cnt_project + cnt_performance + cnt_ops + cnt_support

# 순 사용자 (Active Users): 실제 다운로드(제안서/프로젝트/운영자료/서포트) 기록이 있는 유니크 유저
download_only_df = k_download[k_download['경로 메뉴명'].astype(str).str.contains('프로젝트|운영자료|서포트', na=False)]

active_users_list = pd.concat([
    download_only_df['UserNo'] if not download_only_df.empty else pd.Series(),
    k_proposal['UserNo'] if not k_proposal.empty else pd.Series()
]).unique()
cnt_active_users = len(active_users_list)

# 인당 평균 총 다운로드 수 (0나누기 및 정합성 보정)
avg_dl_per_person = cnt_total_dl / cnt_active_users if cnt_active_users > 0 else 0.0

# KPI 목표 달성률 (목표 56회)
target_value = 56
kpi_attainment = (avg_dl_per_person / target_value) * 100 if target_value > 0 else 0.0


# --- 5. 상단 KPI 카드 ---
kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_metric_card(
        "인당 평균 다운로드",
        f"{avg_dl_per_person:.1f}회",
        desc=f"총 다운로드 ÷ 순사용자 ({_kpi_year}년 1~{_kpi_month}월)"
    )
with kpi_cols[1]:
    render_metric_card(
        "순 사용자 (Active)",
        f"{cnt_active_users:,}명",
        desc="1건 이상 다운로드한 임직원 (중복 제거)"
    )
with kpi_cols[2]:
    render_metric_card(
        "총 다운로드 수",
        f"{cnt_total_dl:,}건",
        desc="제안서 + 프로젝트 찾기 + 프로젝트 실적 + 운영자료 + 서포트"
    )
with kpi_cols[3]:
    attainment_color = "#10b981" if kpi_attainment >= 100 else "#f59e0b"
    render_metric_card(
        "KPI 목표 달성률",
        f"{kpi_attainment:.1f}%",
        delta=(f"목표 {target_value}회", attainment_color),
        desc="인당 평균 다운로드 ÷ 목표 56회 × 100"
    )

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# --- 6. 하단 2열 레이아웃 (1:2 비중) ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown(
        '<div class="headline" style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 4px;">📊 카테고리별 다운로드 비중</div>'
        '<div style="font-size: 12px; color: #64748b; margin-bottom: 12px;">전체 다운로드 건수 중 각 카테고리가 차지하는 비율</div>',
        unsafe_allow_html=True
    )
    # 차트 데이터 구성 (프로젝트 찾기 / 프로젝트 실적 분리)
    ratio_df = pd.DataFrame({
        "구분": ["전체 비중"] * 5,
        "항목": ["제안서", "프로젝트 찾기", "프로젝트 실적", "운영자료", "서포트"],
        "건수": [cnt_proposal, cnt_project, cnt_performance, cnt_ops, cnt_support]
    })
    total_for_ratio = ratio_df["건수"].sum()
    ratio_df["비중(%)"] = (ratio_df["건수"] / total_for_ratio * 100).round(1) if total_for_ratio > 0 else 0

    # 색상 맵핑 정의
    color_map = {
        "제안서":      "#0f172a",   # Deep Navy
        "프로젝트 찾기": "#334155",  # Slate
        "프로젝트 실적": "#7c3aed",  # Purple
        "운영자료":    "#10b981",   # Emerald
        "서포트": "#3b82f6"    # Blue
    }

    # 세로 누적 막대 그래프
    fig_bar = px.bar(
        ratio_df, x="구분", y="비중(%)", color="항목",
        text="비중(%)", 
        color_discrete_map=color_map,
        custom_data=["건수", "항목"]
    )
    fig_bar.update_traces(
        texttemplate='%{text}%', textposition='inside',
        hovertemplate="<b>%{customdata[1]}</b><br>비중: %{y}%<br>총 %{customdata[0]}건<extra></extra>"
    )

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
    st.markdown(
        f'<div class="headline" style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 4px;">📈 월별 다운로드 수 및 누계</div>'
        f'<div style="font-size: 12px; color: #64748b; margin-bottom: 12px;">{_kpi_year}년 1~{_kpi_month}월 · 막대=월별 건수, 선=누계</div>',
        unsafe_allow_html=True
    )

    # 1월~현재월까지만 표시
    months = list(range(1, _kpi_month + 1))

    # 월별 다운로드 집계 (프로젝트·운영자료·서포트 + 제안서)
    monthly_dl = {}
    if not k_download.empty and 'date' in k_download.columns:
        _dl_target = k_download[k_download['경로 메뉴명'].astype(str).str.contains('프로젝트|운영자료|서포트', na=False)]
        monthly_dl = _dl_target.groupby(_dl_target['date'].dt.month).size().to_dict()
    monthly_prop = {}
    if not k_proposal.empty and 'date' in k_proposal.columns:
        monthly_prop = k_proposal.groupby(k_proposal['date'].dt.month).size().to_dict()

    dl_monthly = [monthly_dl.get(m, 0) + monthly_prop.get(m, 0) for m in months]

    # 누계 계산
    dl_cumsum, s = [], 0
    for v in dl_monthly:
        s += v
        dl_cumsum.append(s)

    # 이중 축 그래프 (월별 막대 + 누계 라인)
    fig_line = go.Figure()
    fig_line.add_trace(go.Bar(
        x=[f"{m}월" for m in months], y=dl_monthly,
        name="월별 다운로드", marker_color="#0f172a", opacity=0.8,
        hovertemplate="%{x}: %{y}건<extra></extra>"
    ))
    fig_line.add_trace(go.Scatter(
        x=[f"{m}월" for m in months], y=dl_cumsum,
        name="다운로드 누계", line=dict(color="#10b981", width=3),
        yaxis="y2",
        hovertemplate="%{x} 누계: %{y}건<extra></extra>"
    ))

    fig_line.update_layout(
        height=350, margin=dict(l=20, r=40, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            title=dict(text="월별 다운로드 수", font=dict(color="#0f172a", family='Inter')),
            tickfont=dict(color="#0f172a", family='Inter'),
            showgrid=True, gridcolor='#f1f5f9'
        ),
        yaxis2=dict(
            title=dict(text="누계", font=dict(color="#10b981", family='Inter')),
            tickfont=dict(color="#10b981", family='Inter'),
            overlaying="y", side="right", showgrid=False
        ),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_line, use_container_width=True)

# 하단 정보 안내
st.info(f"""
💡 **KPI 집계 기준 안내**
- **집계 기간:** {_kpi_year}년 1월 1일 ~ {_kpi_month}월 말 (현재 월 기준 · 사이드바 날짜 필터와 무관하게 고정)
- **집계 제외:** AXDX팀·MICE혁신본부(내부 운영팀) / 테스트 계정
- **다운로드 대상:** 제안서(ezPDF DRM) + 프로젝트 찾기 + 프로젝트 실적 + 운영자료 찾기 + 서포트 센터
- **순사용자:** 위 카테고리 중 1건 이상 다운로드한 임직원 수 (중복 제거)
- **인당 평균 다운로드:** 총 다운로드 수 ÷ 순사용자 수
- **KPI 달성률:** 인당 평균 다운로드 ÷ 목표 {target_value}회 × 100
""")


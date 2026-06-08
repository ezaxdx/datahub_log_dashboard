import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config

# --- [UI Style Helper: Metrics] ---
def render_metric_card(label, value, delta=None):
    delta_html = ""
    if delta:
        d_val, d_color = delta
        delta_html = f'<div style="font-size: 11px; font-weight: 700; color: {d_color};">{d_val}</div>'
    
    html = f'<div class="metric-card"><div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;"><div style="color: #64748b; font-size: 13px; font-weight: 700; text-transform: uppercase; font-family: \'Inter\';">{label}</div>{delta_html}</div><div style="color: #1e293b; font-size: 28px; font-weight: 800; font-family: \'Manrope\';">{value}</div></div>'
    st.markdown(html, unsafe_allow_html=True)

# --- [Page Header] ---
st.markdown(f"""
<div class="page-header">
    <div style="font-size: 10px; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-family: 'Inter';">Business Intelligence</div>
    <div style="font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 4px; font-family: 'Manrope';">{config.CURRENT_YEAR} EZ데이터허브 로그 분석 대시보드</div>
    <div style="font-size: 14px; color: #64748b; font-weight: 400; font-family: 'Inter';">사용자의 전반적인 사용량 및 활동 현황을 실시간으로 모니터링합니다.</div>
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
def get_filter_dates():
    # 현재 조회 기간과 이전 비교 기간의 시작/종료일 반환
    today_dt = datetime.now().date()
    curr_start, curr_end = None, None
    prev_start, prev_end = None, None
    
    if date_preset == "오늘":
        curr_start = curr_end = today_dt
        prev_start = prev_end = today_dt - timedelta(days=1)
    elif date_preset == "최근 1주일":
        curr_end = today_dt
        curr_start = today_dt - timedelta(days=7)
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=7)
    elif date_preset == "직접 지정" and date_range and len(date_range) == 2:
        curr_start, curr_end = date_range[0], date_range[1]
        delta_days = (curr_end - curr_start).days + 1
        prev_end = curr_start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=delta_days - 1)
    
    return curr_start, curr_end, prev_start, prev_end

def filter_data(df, start=None, end=None):
    if df.empty: return df
    res = df.copy()
    if 'date' in res.columns and start:
        if end:
            res = res[(res['date'].dt.date >= start) & (res['date'].dt.date <= end)]
        else:
            res = res[res['date'].dt.date >= start]
            
    if sel_dept and '부서' in res.columns:
        res = res[res['부서'].isin(sel_dept)]
    if sel_rank and '직급그룹' in res.columns:
        res = res[res['직급그룹'].isin(sel_rank)]
    return res

# 날짜 계산
c_s, c_e, p_s, p_e = get_filter_dates()

# 현재 기간 데이터
f_login = filter_data(df_login, c_s, c_e)
f_download = filter_data(df_download, c_s, c_e)
f_proposal = filter_data(df_proposal, c_s, c_e)
f_u = filter_data(df_u) # 유저는 기간 필터 제외
# 사용률 분모용: 재직자만 (퇴사자는 분모에서 제외)
f_u_active = f_u[f_u['재직상태'] == '재직'].copy() if '재직상태' in f_u.columns else f_u.copy()

# 이전 기간 데이터 (증감 계산용)
p_login = filter_data(df_login, p_s, p_e)
p_proposal = filter_data(df_proposal, p_s, p_e)
p_download = filter_data(df_download, p_s, p_e)

def calc_delta(curr_val, prev_val):
    if prev_val == 0:
        return ("New", "#6366f1") if curr_val > 0 else ("0%", "#94a3b8")
    diff = ((curr_val - prev_val) / prev_val) * 100
    color = "#10b981" if diff > 0 else ("#ef4444" if diff < 0 else "#94a3b8")
    prefix = "+" if diff > 0 else ""
    return (f"{prefix}{diff:.1f}%", color)

# [수치 정합성] 부서/직급 정보가 없는 데이터를 '정보미등록'으로 채움
for df in [f_login, f_download, f_proposal, f_u]:
    if not df.empty:
        # data.py에서 제공하는 표준 컬럼 사용 및 결측치 최종 보정
        if '부서' in df.columns: 
            df['부서'] = df['부서'].replace(['', None, 'nan', 'NaN'], '정보미등록').fillna('정보미등록')
        if '직급그룹' in df.columns: 
            df['직급그룹'] = df['직급그룹'].replace(['', None, 'nan', 'NaN'], '정보미등록').fillna('정보미등록')

# --- 4. 상단 KPI 섹션 ---
def get_pattern_count(df, pattern):
    if df.empty or '경로 메뉴명' not in df.columns: return 0
    return len(df[df['경로 메뉴명'].astype(str).str.contains(pattern, na=False)])

kpi_cols = st.columns(6)
with kpi_cols[0]:
    d = calc_delta(len(f_login), len(p_login)) if c_s else None
    render_metric_card("총 로그인", f"{len(f_login):,}", d)

with kpi_cols[1]:
    d = calc_delta(len(f_proposal), len(p_proposal)) if c_s else None
    render_metric_card("제안서 DL", f"{len(f_proposal):,}", d)

with kpi_cols[2]:
    curr = get_pattern_count(f_download, '프로젝트 찾기')   # '프로젝트 실적' 중복 제외
    prev = get_pattern_count(p_download, '프로젝트 찾기')
    d = calc_delta(curr, prev) if c_s else None
    render_metric_card("프로젝트 찾기", f"{curr:,}", d)

with kpi_cols[3]:
    curr = get_pattern_count(f_download, '운영자료')
    prev = get_pattern_count(p_download, '운영자료')
    d = calc_delta(curr, prev) if c_s else None
    render_metric_card("운영자료 찾기", f"{curr:,}", d)

with kpi_cols[4]:
    curr = get_pattern_count(f_download, '서포트')
    prev = get_pattern_count(p_download, '서포트')
    d = calc_delta(curr, prev) if c_s else None
    render_metric_card("서포트 센터", f"{curr:,}", d)

with kpi_cols[5]:
    curr = get_pattern_count(f_download, '프로젝트 실적')
    prev = get_pattern_count(p_download, '프로젝트 실적')
    d = calc_delta(curr, prev) if c_s else None
    render_metric_card("프로젝트 실적", f"{curr:,}", d)

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
        # 로그인 수 (라인 + 영역 채우기)
        fig.add_trace(go.Scatter(
            x=all_trends['date'], y=all_trends['로그인수'], 
            name='로그인 수', 
            mode='lines+markers',
            line=dict(color='#0f172a', width=3, shape='spline', smoothing=0.5),
            marker=dict(size=6),
            fill='tozeroy', fillcolor='rgba(15, 23, 42, 0.05)'
        ))
        # 제안서 다운로드 합계 (점선)
        fig.add_trace(go.Scatter(
            x=all_trends['date'], y=all_trends['다운로드합계'],
            name='제안서 다운로드 합계',
            mode='lines+markers',
            line=dict(color='#10b981', width=3, shape='spline', smoothing=0.5, dash='dot'),
            marker=dict(size=6),
            yaxis='y2'
        ))
        
        fig.update_layout(
            height=320, margin=dict(l=40, r=40, t=20, b=40),
            hovermode="x unified",
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1, font=dict(size=11, family='Inter')),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', title=None, rangemode='nonnegative', tickfont=dict(size=10, color="#0f172a", family='Inter')),
            yaxis2=dict(showgrid=False, title=None, rangemode='nonnegative', tickfont=dict(size=10, color="#10b981", family='Inter'), anchor="x", overlaying="y", side="right"),
            xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#64748b", family='Inter'))
        )
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("데이터 없음")

with col_mid_right:
    st.markdown("##### ⚠️ 제안서 다운로드 경고 직원")
    if not f_proposal.empty:
        agg_cols = ['UserNo', '이름', '부서', '직급']
        heavy_users = f_proposal.groupby(agg_cols).size().reset_index(name='횟수')
        heavy_users = heavy_users[heavy_users['횟수'] >= warning_threshold].sort_values(by='횟수', ascending=False).reset_index(drop=True)
        heavy_users.index += 1
        heavy_users.index.name = 'NO.'
        if not heavy_users.empty:
            _n = heavy_users.select_dtypes(include='number').columns.tolist()
            st.dataframe(heavy_users.style.set_properties(subset=_n, **{'text-align': 'center'}), use_container_width=True, hide_index=False, height=180)
        else: st.success("경고 대상 없음")
    else: st.info("데이터 없음")

# --- 6. 하단 2행 (부서/직급별 사용량 및 사용률 분석 - TOP5 표 교체) ---
st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

# 데이터 준비
# 순사용자: 제안서 OR 일반 다운로드 기록 있는 유니크 UserNo (날짜필터 적용, 퇴사자 포함)
# 전체인원: 재직자만 기준 (f_u_active) — 퇴사자는 분모에서 제외
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
login_dept_top5.index += 1
login_dept_top5.index.name = 'NO.'

# 2. 사업부별 사용률 TOP5 (빈 사업부·정보미등록 제외)
_null_divs = {'', 'nan', 'NaN', 'None', '정보미등록'}
_active_div = active_users_all[~active_users_all['사업부'].astype(str).str.strip().isin(_null_divs)]
_fu_div     = f_u_active[~f_u_active['사업부'].astype(str).str.strip().isin(_null_divs)]
active_by_div = _active_div.groupby('사업부')['UserNo'].nunique().reset_index(name='순사용자')
total_users_div = _fu_div.groupby('사업부')['UserNo'].nunique().reset_index(name='전체인원')
usage_div = pd.merge(total_users_div, active_by_div, on='사업부', how='left').fillna(0)
usage_div['전체인원'] = usage_div['전체인원'].astype(int)
usage_div['순사용자'] = usage_div['순사용자'].astype(int)
usage_div['사용률(%)'] = (usage_div['순사용자'] / usage_div['전체인원'] * 100).round(2)
usage_div_top5 = (
    usage_div[['사업부', '전체인원', '순사용자', '사용률(%)']]
    .sort_values('사용률(%)', ascending=False)
    .head(5)
    .reset_index(drop=True)
)
usage_div_top5.index += 1
usage_div_top5.index.name = 'NO.'

# 3. 직급별 로그인 현황
login_rank_all = (
    f_login.groupby('직급').size()
    .reset_index(name='로그인수')
    .sort_values('로그인수', ascending=False)
    .reset_index(drop=True)
)
login_rank_all.index += 1
login_rank_all.index.name = 'NO.'

# 4. 직급별 사용률 현황 (빈 직급·정보미등록 제외)
_null_ranks = {'', 'nan', 'NaN', 'None', '정보미등록'}
_active_rank = active_users_all[~active_users_all['직급'].astype(str).str.strip().isin(_null_ranks)]
_fu_rank     = f_u_active[~f_u_active['직급'].astype(str).str.strip().isin(_null_ranks)]
active_by_rank = _active_rank.groupby('직급')['UserNo'].nunique().reset_index(name='순사용자')
total_users_rank = _fu_rank.groupby('직급')['UserNo'].nunique().reset_index(name='전체인원')
usage_rank = pd.merge(total_users_rank, active_by_rank, on='직급', how='left').fillna(0)
usage_rank['전체인원'] = usage_rank['전체인원'].astype(int)
usage_rank['순사용자'] = usage_rank['순사용자'].astype(int)
usage_rank['사용률(%)'] = (usage_rank['순사용자'] / usage_rank['전체인원'] * 100).round(2)
usage_rank_all = (
    usage_rank[['직급', '전체인원', '순사용자', '사용률(%)']]
    .sort_values('사용률(%)', ascending=False)
    .reset_index(drop=True)
)
usage_rank_all.index += 1
usage_rank_all.index.name = 'NO.'

# 레이아웃 배치 (1행 4열 표 교체)
col_t1, col_t2, col_t3, col_t4 = st.columns(4)
table_height = 210

def _num_center(df):
    """숫자형 컬럼 가운데 정렬 + 사용률 소수점 2자리 포맷 Styler"""
    num_cols = df.select_dtypes(include='number').columns.tolist()
    fmt = {col: '{:.2f}' for col in num_cols if '사용률' in col}
    return df.style.set_properties(subset=num_cols, **{'text-align': 'center'}).format(fmt)

with col_t1:
    st.markdown("##### 부서별 로그인 TOP5")
    st.dataframe(_num_center(login_dept_top5), use_container_width=True, hide_index=False, height=table_height)

with col_t2:
    st.markdown("##### 사업부별 사용률 TOP5")
    st.dataframe(_num_center(usage_div_top5), use_container_width=True, hide_index=False, height=table_height)

with col_t3:
    st.markdown("##### 직급별 로그인 현황")
    st.dataframe(_num_center(login_rank_all), use_container_width=True, hide_index=False, height=table_height)

with col_t4:
    st.markdown("##### 직급별 사용률 현황")
    st.dataframe(_num_center(usage_rank_all), use_container_width=True, hide_index=False, height=table_height)
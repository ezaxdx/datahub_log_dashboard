import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import config

# --- [UI Helper: Metric Card] ---
def render_metric_card(label, value, color="#6366f1"):
    st.markdown(f"""
    <div class="metric-card" style="text-align: center;">
        <div style="color: #64748b; font-size: 12px; font-weight: 500; margin-bottom: 4px;">{label}</div>
        <div style="color: #1e293b; font-size: 22px; font-weight: 700;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- [Page Header: Boxed Banner] ---
st.markdown(f"""
<div class="page-header" style="padding: 12px 24px; margin-bottom: 16px;">
    <div style="font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; opacity: 0.8;">Overview</div>
    <div style="font-size: 24px; font-weight: 800; margin-bottom: 4px;"> {config.CURRENT_YEAR} 통합 로그 분석 대시보드</div>
    <div style="font-size: 13px; opacity: 0.85; font-weight: 400;">데이터허브 시스템의 전반적인 사용량 및 활동 지표를 모니터링합니다.</div>
</div>
""", unsafe_allow_html=True)

# --- 1. 데이터 가져오기 ---
df_login = st.session_state.get('df_login', pd.DataFrame())
df_download = st.session_state.get('df_download', pd.DataFrame())
df_proposal = st.session_state.get('df_proposal', pd.DataFrame())

# --- 2. 필터 값 가져오기 ---
date_preset = st.session_state.get('date_preset', '전체')
date_range = st.session_state.get('date_range', None)
sel_dept = st.session_state.get('sel_dept', [])
sel_rank = st.session_state.get('sel_rank', [])
warning_threshold = st.session_state.get('warning_threshold', 10)

# --- 3. 필터링 함수 ---
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
    if sel_rank and '직급그룹' in res.columns:
        res = res[res['직급그룹'].isin(sel_rank)]
    return res

f_login = filter_data(df_login)
f_download = filter_data(df_download)
f_proposal = filter_data(df_proposal)

# --- 4. 프리미엄 KPI 섹션 (박스형 카드) ---
st.markdown("### Key Performance Indicators")
c1, c2, c3, c4, c5 = st.columns(5)

def get_menu_count(df, pattern):
    if df.empty or '경로 메뉴명' not in df.columns: return 0
    return len(df[df['경로 메뉴명'].astype(str).str.contains(pattern, na=False)])

with c1: render_metric_card("총 로그인", f"{len(f_login):,}건", "#6366f1")
with c2: render_metric_card("제안서 DL", f"{len(f_proposal):,}건", "#f59e0b")
with c3: render_metric_card("프로젝트 찾기", f"{get_menu_count(f_download, '프로젝트'):,}건", "#10b981")
with c4: render_metric_card("운영자료 찾기", f"{get_menu_count(f_download, '운영자료'):,}건", "#3b82f6")
with c5: render_metric_card("서포트 센터", f"{get_menu_count(f_download, '서포트'):,}건", "#ec4899")

st.markdown("<br>", unsafe_allow_html=True)

# --- 5. 차트 섹션 (모던 카드 스타일) ---
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("""
    <div style="padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 10px;">
        <h3 style="margin: 0; padding: 0;">일자별 활동 현황</h3>
    </div>
    """, unsafe_allow_html=True)
    if not f_login.empty and 'date' in f_login.columns:
        daily_logs = f_login.groupby(f_login['date'].dt.date).size().reset_index(name='방문건수')
        daily_logs.columns = ['날짜', '방문건수']
        fig = px.line(daily_logs, x='날짜', y='방문건수', markers=True, color_discrete_sequence=['#6366f1'])
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=20), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

with col_chart2:
    st.markdown("""
    <div style="padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 10px;">
        <h3 style="margin: 0; padding: 0;">부서별 사용 비중</h3>
    </div>
    """, unsafe_allow_html=True)
    if not f_login.empty and '부서' in f_login.columns:
        dept_stats = f_login['부서'].value_counts().reset_index()
        dept_stats.columns = ['부서명', '활동건수']
        fig = px.pie(dept_stats, values='활동건수', names='부서명', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=10, b=20), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

# --- 6. 상세 테이블 섹션 ---
st.markdown("---")
st.markdown("###  직원별 활동 상세 내역")

candidate_cols = ['UserNo', '이름', '부서', '직급', config.COL_NAME_EMAIL]
user_stats = pd.DataFrame()

# 로그인 합산
if not f_login.empty:
    l_grp = [c for c in candidate_cols if c in f_login.columns]
    if l_grp: user_stats = f_login.groupby(l_grp).size().reset_index(name='로그인수')

# 제안서 DL 합산
if not f_proposal.empty:
    p_grp = [c for c in candidate_cols if c in f_proposal.columns]
    if p_grp:
        p_stats = f_proposal.groupby(p_grp).size().reset_index(name='제안서 DL')
        if user_stats.empty:
            user_stats = p_stats
            user_stats['로그인수'] = 0
        else:
            common = list(set(user_stats.columns).intersection(set(p_grp)))
            user_stats = pd.merge(user_stats, p_stats, on=common, how='outer')

# 메뉴별 합산
def get_user_menu_stats(df, pattern, name):
    if df.empty or '경로 메뉴명' not in df.columns: return pd.DataFrame()
    sub_df = df[df['경로 메뉴명'].astype(str).str.contains(pattern, na=False)]
    if sub_df.empty: return pd.DataFrame()
    m_grp = [c for c in candidate_cols if c in sub_df.columns]
    return sub_df.groupby(m_grp).size().reset_index(name=name)

for p, n in [("프로젝트", "프로젝트"), ("운영자료", "운영자료"), ("서포트", "서포트센터")]:
    m_df = get_user_menu_stats(f_download, p, n)
    if not m_df.empty:
        if user_stats.empty:
            user_stats = m_df
        else:
            common = list(set(user_stats.columns).intersection(set(m_df.columns)))
            user_stats = pd.merge(user_stats, m_df, on=common, how='left')

if not user_stats.empty:
    cols_to_fill = ['로그인수', '제안서 DL', '프로젝트', '운영자료', '서포트센터']
    for c in cols_to_fill:
        if c not in user_stats.columns: user_stats[c] = 0
        user_stats[c] = user_stats[c].fillna(0).astype(int)
    
    # user_stats['합계'] = user_stats[cols_to_fill].sum(axis=1)
    user_stats = user_stats.sort_values(by=cols_to_fill[0], ascending=False)
    
    # 테이블 스타일링 (제안서 DL 10회 이상 배경 붉은색)
    def highlight_dl(val):
        if isinstance(val, (int, float)) and val >= 10:
            return 'background-color: #fee2e2; color: #000000;'
        return ''
    
    try:
        styled_df = user_stats.style.map(highlight_dl, subset=['제안서 DL'])
    except AttributeError:
        styled_df = user_stats.style.applymap(highlight_dl, subset=['제안서 DL'])
        
    st.dataframe(styled_df, use_container_width=True, hide_index=True)
else:
    st.info("데이터가 없습니다.")

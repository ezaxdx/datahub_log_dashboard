import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import config
import data
import os

st.set_page_config(page_title="EZ데이터허브 사용 로그 대시보드",layout="wide")

# --- [UI Style Customization] ---
# Font Awesome CDN & Global SaaS Layout CSS
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    /* 메인 배경색 및 폰트 */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        width: 280px !important;
    }
    
    /* 커스텀 네비게이션 버튼 스타일 */
    .nav-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 4px 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
        color: #64748b;
        font-weight: 500;
        border: none;
        background: none;
        width: 90%;
        text-align: left;
    }
    
    .nav-item:hover {
        background-color: #f1f5f9;
        color: #6366f1;
    }
    
    .nav-item.active {
        background-color: #6366f1;
        color: #ffffff !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4);
    }
    
    .nav-item i {
        margin-right: 12px;
        font-size: 18px;
        width: 24px;
        text-align: center;
    }

    /* 메트릭 카드 스타일 */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* 섹션 배너 스타일 */
    .page-header {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 1. 데이터 로드 및 세션 상태 저장 ---
reload_requested = st.sidebar.button("🔄 최신 데이터 동기화", use_container_width=True)
if 'df_users' not in st.session_state or reload_requested:
    with st.spinner("데이터 동기화 중..."):
        try:
            data.load_all.clear()
            df_users, df_login, df_download, df_proposal = data.run_all()
            st.session_state['df_users'] = df_users
            st.session_state['df_login'] = df_login
            st.session_state['df_download'] = df_download
            st.session_state['df_proposal'] = df_proposal
            st.session_state['last_refresh'] = datetime.now()
            if 'warning_threshold' not in st.session_state:
                st.session_state['warning_threshold'] = 10
            st.toast("데이터 로드 완료!")
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {e}")
            st.stop()

# --- 2. 사이드바 구성 ---

# A. 유저 정보 (이미지 2번 스타일)
st.sidebar.markdown(f"""
<div style="display: flex; align-items: center; padding: 20px 12px; margin-bottom: 10px;">
    <div style="background-color: #6366f1; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; margin-right: 12px;">
        EZ
    </div>
    <div>
        <div style="font-weight: 700; color: #1e293b; font-size: 15px;">EZ_AXDX</div>
        <div style="color: #64748b; font-size: 12px;">Log Dashboard v4</div>
    </div>
</div>
""", unsafe_allow_html=True)

# B. D+ 카운터 카드
today = datetime.now().date()
base_date = datetime.strptime(config.BASE_DATE, "%Y-%m-%d").date()
df_login = st.session_state['df_login']
latest_log_date = df_login['date'].max().date() if not df_login.empty and 'date' in df_login.columns else today
days_elapsed = (today - base_date).days

st.sidebar.markdown(f"""
<div style="background-color: #f1f5f9; border-radius: 12px; padding: 12px; margin: 0 12px 20px 12px; text-align: center;">
    <div style="font-size: 10px; color: #64748b; margin-bottom: 2px;">SERVICE DAYS</div>
    <div style="font-size: 20px; font-weight: 800; color: #1e293b;">D+{days_elapsed}</div>
</div>
""", unsafe_allow_html=True)

# C. 메뉴 (네비게이션)
st.sidebar.markdown('<p style="font-size: 11px; font-weight: 700; color: #94a3b8; margin-left: 20px; margin-bottom: 8px;">DASHBOARD MENUS</p>', unsafe_allow_html=True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pages = {
    "Total Dashboard": {"path": os.path.join(BASE_DIR, "pages", "1_total.py"), "icon": "fa-chart-line"},
    "File Analysis":   {"path": os.path.join(BASE_DIR, "pages", "2_File_Analysis.py"), "icon": "fa-file-shield"},
    "Dept & Team":     {"path": os.path.join(BASE_DIR, "pages", "3_department.py"), "icon": "fa-building-columns"},
    "Check KPI":       {"path": os.path.join(BASE_DIR, "pages", "4_kpi.py"), "icon": "fa-circle-check"},
    "Employee List":   {"path": os.path.join(BASE_DIR, "pages", "5_employee_list.py"), "icon": "fa-users-viewfinder"}
}

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Total Dashboard"

for name, info in pages.items():
    is_active = st.session_state['current_page'] == name
    active_class = "active" if is_active else ""
    
    # 사이드바 버튼으로 메뉴 구현 (CSS 활용)
    if st.sidebar.button(name, key=f"nav_{name}", use_container_width=True, type="secondary" if not is_active else "primary"):
        st.session_state['current_page'] = name
        st.rerun()

st.sidebar.markdown("---")

# D. 상세 필터 (익스팬더)
with st.sidebar.expander("🔍 상세 필터 (조회 기준)", expanded=False):
    date_preset = st.radio("날짜 선택", ["최근 1주일", "오늘", "전체", "직접 지정"], index=0, horizontal=True)
    date_range = None
    if date_preset == "직접 지정":
        date_range = st.date_input("조회 기간", [today - timedelta(days=7), today])
    elif date_preset == "최근 1주일":
        date_range = [today - timedelta(days=7), today]
    elif date_preset == "오늘":
        date_range = [today, today]
    
    st.session_state['date_preset'] = date_preset
    st.session_state['date_range'] = date_range

    st.markdown("---")
    df_u = st.session_state['df_users']
    dept_col = config.YEAR_COL_DEPT.format(year=config.CURRENT_YEAR)
    hq_col = config.YEAR_COL_HQ.format(year=config.CURRENT_YEAR)
    div_col  = config.YEAR_COL_DIVISION.format(year=config.CURRENT_YEAR)

    if not df_u.empty:
        # data.py에서 이미 표준화된 '부서' 및 '_ui_dept'가 제공됨
        all_depts = sorted(df_u['_ui_dept'].unique().tolist())
        
        exclude_userno = config.DEFAULT_EXCLUDE_USERNO
        exclude_names = df_u[df_u['UserNo'].isin(exclude_userno)]['_ui_dept'].tolist()
        exclude_depts = config.DEFAULT_EXCLUDE_DEPTS + exclude_names
        
        default_depts = [d for d in all_depts if d not in exclude_depts]

        col_dept1, col_dept2 = st.columns([3, 1])
        with col_dept1:
            sel_dept = st.multiselect("부서명", options=all_depts, default=default_depts)
        with col_dept2:
            if st.button("전체", key="dept_select_all"):
                sel_dept = all_depts
        
        st.session_state['sel_dept'] = sel_dept
        st.session_state['sel_rank'] = st.multiselect("직급 그룹", options=['실무자(사원/대리)', '관리자(차장↑)', '임원'])

# --- 3. 선택된 페이지 실행 ---
current_page_info = pages[st.session_state['current_page']]
page_path = current_page_info['path']

if os.path.exists(page_path):
    with open(page_path, encoding='utf-8') as f:
        code = f.read()
        # globals() 대신 exec를 활용하되 페이지 내 UI가 올바르게 렌더링되도록 처리
        exec(code, globals())
else:
    st.error(f"페이지 파일을 찾을 수 없습니다: {page_path}")
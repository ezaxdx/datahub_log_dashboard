import streamlit as st
# Force redeploy: 2026-05-06 17:10
import pandas as pd
from datetime import datetime, timedelta, date as date_type
import config
import data
import os
import notifier  # 추가

st.set_page_config(page_title="EZ데이터허브 사용 로그 대시보드",layout="wide")

# --- [UI Style Customization] ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
<style>
    /* 전역 폰트 및 배경 설정 */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f7f9fb;
    }
    
    h1, h2, h3, h4, h5, h6, .headline {
        font-family: 'Manrope', sans-serif;
    }

    /* 사이드바 스타일링 */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
        padding-top: 20px;
    }
    
    /* 사이드바 내 버튼 스타일 (네비게이션) */
    div[data-testid="stVerticalBlock"] > div > div > button {
        border: none !important;
        background-color: transparent !important;
        color: #64748b !important;
        text-align: left !important;
        padding: 10px 16px !important;
        width: 100% !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        display: flex !important;
        align-items: center !important;
    }

    /* 마우스 호버 효과 */
    div[data-testid="stVerticalBlock"] > div > div > button:hover {
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
    }

    /* 활성화된 버튼 스타일 (Primary 버튼 활용) */
    div[data-testid="stVerticalBlock"] > div > div > button[kind="primary"] {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border-left: 4px solid #0f172a !important;
        border-radius: 4px 10px 10px 4px !important;
    }

    /* 메트릭 카드 스타일 */
    .metric-card {
        background-color: #ffffff;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
    }
    
    /* 페이지 헤더 스타일 */
    .page-header {
        background-color: #ffffff;
        padding: 32px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        margin-bottom: 32px;
    }

    /* Dataframe 제목행 흰색 배경 (canvas 렌더러) */
    [data-testid="stDataFrame"] [role="columnheader"],
    [data-testid="stDataFrame"] th {
        background-color: #ffffff !important;
        color: #1e293b !important;
        font-weight: 700 !important;
    }
    /* Pandas Styler 기반 테이블: NO. 인덱스 + 열 헤더 흰색/가운데 */
    th.row_heading, th.col_heading, th.blank {
        background-color: #ffffff !important;
        text-align: center !important;
        color: #1e293b !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. 데이터 로드 및 세션 상태 저장 ---
reload_requested = st.sidebar.button("🔄 최신 데이터 동기화", use_container_width=True)
if 'df_users' not in st.session_state or reload_requested:
    with st.spinner("데이터 동기화 중..."):
        try:
            data.load_all.clear()
            data.load_from_api.clear()  # REST_API 모드 캐시도 함께 초기화
            df_users, df_login, df_download, df_proposal = data.run_all()

            # 재직 상태 수동 오버라이드 적용 (status_overrides.json)
            try:
                import json as _json
                _ov_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status_overrides.json")
                if os.path.exists(_ov_path) and not df_users.empty and 'UserNo' in df_users.columns:
                    with open(_ov_path, 'r', encoding='utf-8') as _f:
                        _overrides = _json.load(_f)
                    for _uno, _status in _overrides.items():
                        _mask = df_users['UserNo'] == str(_uno)
                        df_users.loc[_mask, '재직상태'] = _status
            except Exception:
                pass

            # 프로필 수동 오버라이드 적용 (profile_overrides.json)
            # 부서·직급·사업부 등 API 미등록 항목 수동 보정
            try:
                import json as _json
                _po_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile_overrides.json")
                if os.path.exists(_po_path) and not df_users.empty and 'UserNo' in df_users.columns:
                    with open(_po_path, 'r', encoding='utf-8') as _f:
                        _profiles = _json.load(_f)
                    for _uno, _fields in _profiles.items():
                        _mask = df_users['UserNo'] == str(_uno)
                        for _col, _val in _fields.items():
                            if _col in df_users.columns:
                                df_users.loc[_mask, _col] = _val
            except Exception:
                pass

            st.session_state['df_users'] = df_users
            st.session_state['df_login'] = df_login
            st.session_state['df_download'] = df_download
            st.session_state['df_proposal'] = df_proposal
            st.session_state['last_refresh'] = datetime.now()
            if 'warning_threshold' not in st.session_state:
                st.session_state['warning_threshold'] = 10
            # --- [자동 위험 감지 및 이메일 알림] ---
            try:
                status = notifier.run_auto_check(df_proposal, df_download)
                if status and "message" in status:
                    if status["status"] == "alert":
                        st.toast(f"데이터 로드 완료! {status['message']}", icon="🚨")
                    else:
                        st.toast(f"데이터 로드 완료! {status['message']}", icon="✅")
                else:
                    st.toast("데이터 로드 완료!")
            except Exception as notify_e:
                print(f"알림 발송 중 오류 발생: {notify_e}")
                st.toast("데이터 로드 완료! (알림 점검 중 오류발생)", icon="⚠️")
                
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {e}")
            st.stop()

# --- 2. 사이드바 구성 ---

# A. 브랜드 로고 (이미지 스타일)
st.sidebar.markdown(f"""
<div style="display: flex; align-items: center; padding: 24px 12px; margin-bottom: 20px; font-family: 'Manrope';">
    <div style="background-color: #1e293b; width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; margin-right: 14px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
        <i class="fa-solid fa-database" style="font-size: 20px;"></i>
    </div>
    <div>
        <div style="font-weight: 800; color: #1e293b; font-size: 18px; line-height: 1.2;">EZ Data Hub</div>
        <div style="color: #64748b; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Business Intelligence</div>
    </div>
</div>
""", unsafe_allow_html=True)

# B. D+ 카운터 (상단 우측 또는 하단 배치 고민 가능하나 일단 사이드바 유지)
today = datetime.now().date()
base_date = datetime.strptime(config.BASE_DATE, "%Y-%m-%d").date()
df_login = st.session_state['df_login']
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

# C. 메뉴 (네비게이션)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

pages = {
    "Total Dashboard": {"path": os.path.join(BASE_DIR, "pages", "1_total.py"), "icon": "fa-table-columns"},
    "File Analysis":   {"path": os.path.join(BASE_DIR, "pages", "2_File_Analysis.py"), "icon": "fa-file-shield"},
    "Dept & Team":     {"path": os.path.join(BASE_DIR, "pages", "3_department.py"), "icon": "fa-users-gear"},
    "Check KPI":       {"path": os.path.join(BASE_DIR, "pages", "4_kpi.py"), "icon": "fa-circle-check"},
    "Employee List":   {"path": os.path.join(BASE_DIR, "pages", "5_employee_list.py"), "icon": "fa-address-book"}
}

if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Total Dashboard"

for name, info in pages.items():
    is_active = st.session_state['current_page'] == name
    
    # 아이콘과 함께 버튼 생성
    if st.sidebar.button(name, key=f"nav_{name}", use_container_width=True, type="primary" if is_active else "secondary"):
        st.session_state['current_page'] = name
        st.rerun()

st.sidebar.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# E. 하단 유틸리티 (이미지 스타일 준수)
st.sidebar.markdown("""
<div style="padding: 0 12px;">
    <div style="background-color: #1e293b; color: white; padding: 12px; border-radius: 8px; text-align: center; font-size: 13px; font-weight: 600; margin-bottom: 8px; cursor: pointer;">
        <i class="fa-solid fa-download" style="margin-right: 8px;"></i> Download Report
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("---")

# E. 상세 필터 (익스팬더)
with st.sidebar.expander("🔍 Filter View", expanded=False):
    # 날짜 프리셋 유지 로직
    presets = ["최근 1주일", "오늘", "전체", "직접 지정"]
    saved_preset = st.session_state.get('date_preset', "최근 1주일")
    try:
        preset_index = presets.index(saved_preset)
    except:
        preset_index = 0
        
    date_preset = st.radio("날짜 선택", presets, index=preset_index, horizontal=True)
    
    date_range = None
    if date_preset == "직접 지정":
        # 이전 선택값 복원 (None·비정상 타입 방어)
        _saved = st.session_state.get('date_range', None)
        def _to_date(v):
            try:
                if hasattr(v, 'date') and callable(v.date): return v.date()
                if isinstance(v, date_type): return v
                return date_type.fromisoformat(str(v)[:10])
            except Exception:
                return today
        if isinstance(_saved, (list, tuple)) and len(_saved) >= 2:
            _def_start, _def_end = _to_date(_saved[0]), _to_date(_saved[1])
        else:
            _def_start, _def_end = today - timedelta(days=7), today

        # 시작일 / 종료일 개별 선택 (범위 선택보다 클릭이 쉬움)
        _col_s, _col_e = st.columns(2)
        with _col_s:
            _start = st.date_input("시작일", value=_def_start, key="date_start")
        with _col_e:
            _end = st.date_input("종료일", value=_def_end, key="date_end")

        # 시작일 > 종료일이면 자동 교정
        if _start > _end:
            _end = _start
        date_range = [_start, _end]
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
        
        # 기본 선택될 부서 리스트 먼저 정의
        default_depts = [d for d in all_depts if d not in exclude_depts]

        # 부서 선택 유지 로직
        saved_sel_dept = st.session_state.get('sel_dept', default_depts)
        # 선택된 부서가 전체 리스트에 여전히 존재하는지 확인 (방어 로직)
        valid_sel_dept = [d for d in saved_sel_dept if d in all_depts]

        col_dept1, col_dept2 = st.columns([3, 1])
        with col_dept1:
            sel_dept = st.multiselect("부서명", options=all_depts, default=valid_sel_dept)
        with col_dept2:
            if st.button("전체", key="dept_select_all"):
                st.session_state['sel_dept'] = all_depts  # rerun 전 session_state 먼저 갱신
                st.rerun()
        
        st.session_state['sel_dept'] = sel_dept
        
        # 직급 그룹 유지 로직
        saved_sel_rank = st.session_state.get('sel_rank', [])
        st.session_state['sel_rank'] = st.multiselect("직급 그룹", options=['실무자(사원/대리)', '관리자(차장↑)', '임원'], default=saved_sel_rank)

# F. 알림 자동화 로그
_log_path = os.path.join(BASE_DIR, "checkpoints", "notifier_log.txt")
with st.sidebar.expander("🔔 알림 자동화 로그", expanded=False):
    if os.path.exists(_log_path):
        try:
            _log_text = None
            for _enc in ['utf-16', 'utf-8', 'cp949']:
                try:
                    with open(_log_path, 'r', encoding=_enc) as _f:
                        _log_text = _f.read()
                    break
                except Exception:
                    continue
            if _log_text:
                _lines = [l.strip() for l in _log_text.splitlines() if l.strip()]
                _key_lines = [l for l in _lines if any(k in l for k in
                    ['알림 체크', 'Notifier', 'Email', '이메일', '알림 기준', '위험 인원', '신규 알림', '구간'])]
                if _key_lines:
                    for _line in _key_lines[-10:]:
                        if '위험 인원' in _line or 'alert' in _line.lower():
                            st.markdown(f"🚨 `{_line}`")
                        elif '완료' in _line or 'ok' in _line.lower():
                            st.markdown(f"✅ `{_line}`")
                        else:
                            st.markdown(f"ℹ️ `{_line}`")
                else:
                    st.caption("로그 기록 없음")
            else:
                st.caption("로그를 읽을 수 없습니다.")
        except Exception as _e:
            st.caption(f"로그 읽기 오류: {_e}")
    else:
        st.caption("아직 실행 기록이 없습니다.\n작업 스케줄러가 실행되면 여기에 표시됩니다.")

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
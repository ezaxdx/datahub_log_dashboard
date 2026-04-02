import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Antigravity 대시보드", layout="wide")

# --- 1. 데이터 연결 및 로드 (ANTIGRAVITY Logic) ---
@st.cache_data(ttl=600)
def load_data():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # 중복 컬럼명 처리 함수 (브라우저1, 브라우저2 등) 및 없는 시트 방어 로직 추가
    def get_df_with_unique_columns(worksheet_name):
        try:
            ws = sh.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            return pd.DataFrame()
        
        data = ws.get_all_values()
        if not data:
            return pd.DataFrame()
        
        headers = data[0]
        from collections import Counter
        col_counts = Counter(headers)
        
        running_counts = {}
        new_headers = []
        for col in headers:
            if col_counts[col] > 1:
                running_counts[col] = running_counts.get(col, 0) + 1
                new_headers.append(f"{col}{running_counts[col]}")
            else:
                new_headers.append(col)
                
        df = pd.DataFrame(data[1:], columns=new_headers)
        # Type 유추 (get_all_records와 동일하게 숫자형 자동 변환 위함)
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        return df

    # 각 시트 데이터 프레임화
    df_login = get_df_with_unique_columns("login")
    df_download = get_df_with_unique_columns("download")
    df_proposal = get_df_with_unique_columns("제안서_ezPDF")
    
    # 직원정보 시트는 병합 헤더로 인해 별도 처리 (2026년 기준)
    df_users = pd.DataFrame()
    try:
        emp_data = sh.worksheet("직원정보").get_all_values()
        if len(emp_data) > 2:
            records = []
            for row in emp_data[2:]:
                if len(row) > 12:
                    # UserNo는 3자리 고정 (ex: '1' -> '001')
                    raw_no = str(row[0]).strip()
                    if not raw_no: continue
                    
                    # .0 등의 소수점 찌꺼기가 문자열 역변환 시 있을수 있으므로 제거
                    if raw_no.endswith('.0'): raw_no = raw_no[:-2]
                    no = raw_no.zfill(3)
                    
                    name = str(row[1]).strip()
                    
                    # 2026년 데이터만 사용 (퇴사자 제외 위해 빈칸이면 제외)
                    hq26 = str(row[7]).strip()
                    dept26 = str(row[8]).strip()
                    rank26 = str(row[11]).strip()
                    email = str(row[12]).strip()
                    
                    # 부서명(2026) -> 본부/실(2026) 순
                    final_dept = dept26 if dept26 else hq26
                    
                    records.append({
                        # 직원정보의 'No'는 사번이 아니므로 제거
                        "이름": name,
                        "부서": final_dept,
                        "직급": rank26,
                        "이메일": email
                    })
            df_users = pd.DataFrame(records)
    except Exception as e:
        df_users = pd.DataFrame()
    
    return df_login, df_download, df_proposal, df_users

# 예외 처리를 추가하여 로컬에서 에러 없이 UI를 확인할 수 있도록 함
try:
    login_raw, download_raw, proposal_raw, user_master = load_data()

    # --- 2. 데이터 전처리 및 매핑 ---
    # 1. Rosetta Stone: download 시트에서 UserNo <-> 이메일(사용자ID) 교차 매핑 브릿지 생성
    userno_to_email = {}
    email_to_userno = {}
    if not download_raw.empty:
        d_ucol = 'userNo' if 'userNo' in download_raw.columns else 'UserNo' if 'UserNo' in download_raw.columns else None
        if d_ucol and '사용자ID' in download_raw.columns:
            for _, r in download_raw.iterrows():
                uno = str(r[d_ucol]).strip().replace('.0', '').zfill(3)
                uid = str(r['사용자ID']).strip()
                if uno and uid and uno != 'nan' and uid != 'nan':
                    userno_to_email[uno] = uid
                    email_to_userno[uid] = uno

    def preprocess_data(df, sheet_name=""):
        if df.empty: return df
        # 동적 날짜(로그인 일자, 다운로드 일자 등)를 date 통일 (등록일 우선 처리)
        for date_col in ['등록일', '다운로드 일자', '로그인 일자']:
            if date_col in df.columns:
                df['date'] = pd.to_datetime(df[date_col], errors='coerce')
                break
        
        # --- 유저 요청: 다운로드 브릿지를 통한 이메일 마스터 병합 ---
        if not user_master.empty:
            orig_name = df['이름'].copy() if '이름' in df.columns else pd.Series()
            
            # 기존 직급 등 삭제
            cols_to_drop = [c for c in ['이름', '부서', '부서명', '본부명', '팀', '직위', '직급', '통계 직급', '직책'] if c in df.columns]
            df.drop(columns=cols_to_drop, inplace=True)
            
            u_col = 'userNo' if 'userNo' in df.columns else 'UserNo' if 'UserNo' in df.columns else None
            
            # 브릿지를 이용해 양쪽 키 보충
            if u_col and '사용자ID' not in df.columns:
                df[u_col] = df[u_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(3)
                df['사용자ID'] = df[u_col].map(userno_to_email)
            elif '사용자ID' in df.columns and not u_col:
                df['사용자ID'] = df['사용자ID'].astype(str).str.strip()
                df['UserNo'] = df['사용자ID'].map(email_to_userno)
                u_col = 'UserNo'
            elif u_col and '사용자ID' in df.columns:
                df[u_col] = df[u_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(3)
                df['사용자ID'] = df['사용자ID'].astype(str).str.strip()

            # 이메일 기준으로 마스터 조인
            if '사용자ID' in df.columns:
                # 빈 이메일 문자열 간의 카테시안 조인(데이터 증식)을 막기 위해 NaN 처리
                df['사용자ID'] = df['사용자ID'].replace("", pd.NA)
                
                # 마스터 이메일 또한 빈칸 및 중복을 제거하여 1:1 매핑만 허용
                valid_master = user_master[user_master['이메일'].astype(str).str.strip() != ""].drop_duplicates(subset=['이메일'])
                
                df = pd.merge(df, valid_master[['이메일', '이름', '부서', '직급']], left_on='사용자ID', right_on='이메일', how='left')

            # 이메일 브릿지가 없어 조인이 안 된 행 구제 (이름 기준 Fallback)
            if not orig_name.empty:
                name_dict = user_master.set_index('이름')[['부서', '직급']].to_dict('index')
                if '이름' not in df.columns: df['이름'] = orig_name
                else: df['이름'] = df['이름'].fillna(orig_name)
                
                if '부서' not in df.columns: df['부서'] = ""
                if '직급' not in df.columns: df['직급'] = ""
                
                def apply_fallback(r):
                    n = str(r.get('이름', '')).strip()
                    if n and n in name_dict:
                        if pd.isna(r.get('부서')) or not str(r.get('부서')).strip(): r['부서'] = name_dict[n]['부서']
                        if pd.isna(r.get('직급')) or not str(r.get('직급')).strip(): r['직급'] = name_dict[n]['직급']
                    return r
                df = df.apply(apply_fallback, axis=1)

        # 유저 요청에 따라 기존에 제외했던 모든 특수 사업부서(개발, MICE 등) 복구
        return df

    df_login = preprocess_data(login_raw, "login")
    df_download = preprocess_data(download_raw, "download")
    df_proposal = preprocess_data(proposal_raw, "제안서_ezPDF")

    # 직급 그룹화 (실무자 vs 관리자)
    def group_rank(rank):
        if pd.isna(rank): return '기타'
        rank_str = str(rank).strip()
        if rank_str in ['사원', '대리', '주임', '연구원']: return '실무자(사원/대리)'
        if rank_str in ['차장', '팀장', '부장', '본부장', '이사', '실장', '수석', '상무', '전무']: return '관리자(차장↑)'
        return '기타'

    for df in [df_login, df_download, df_proposal]:
        if '직급' in df.columns:
            df['직급그룹'] = df['직급'].apply(group_rank)

    # --- 3. 사이드바: D+nn 날짜 카운터 ---
    today = datetime.now().date()
    
    # 이사님 산정 기준 오픈일 (2026-03-19 기준 D+426일이 되도록 역산)
    base_date = datetime(2025, 1, 17).date()
    
    if not df_login.empty and 'date' in df_login.columns:
        valid_dates = df_login['date'].dropna()
        latest_date = valid_dates.max().date() if not valid_dates.empty else today
    else:
        latest_date = today
    
    days_elapsed = (today - base_date).days
    days_since_last = (today - latest_date).days
    
    st.sidebar.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 8px;
    border-left: 4px solid #e94560;
    text-align: center;
">
    <div style="color:#aaa; font-size:11px; margin-bottom:4px;">📅 서비스 운영 기준일 ({base_date.strftime('%Y.%m.%d')}~)</div>
    <div style="color:#fff; font-size:28px; font-weight:900; letter-spacing:1px;">D+{days_elapsed}</div>
    <div style="color:#aaa; font-size:11px; margin-top:4px;">최근 로그: {latest_date.strftime('%Y.%m.%d')} (D+{(latest_date - base_date).days})</div>
</div>
""", unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # 최신 데이터 강제 불러오기 (캐시 초기화)
    if st.sidebar.button("🔄 구글 시트 최신화 (새로고침)", use_container_width=True):
        load_data.clear()
        st.rerun()

    st.sidebar.header("🔍 상세 필터")
    
    # 1. 날짜 빠른 선택
    date_preset = st.sidebar.radio(
        "날짜 빠른 선택",
        ["최근 1주일", "오늘", "전체", "직접 지정"],
        index=0,
        horizontal=True
    )
    
    date_range = None
    if date_preset == "직접 지정":
        default_start = today - timedelta(days=7)
        date_range = st.sidebar.date_input("조회 기간 (시작일~종료일)", [default_start, today])

    # 실제 데이터에서 부서 목록 추출
    all_depts = set()
    for dff in [df_login, df_download, df_proposal]:
        if not dff.empty and '부서' in dff.columns:
            all_depts.update(dff['부서'].dropna().astype(str).unique())
    all_depts = sorted(list(x for x in all_depts if x and x != "nan"))
            
    sel_dept = st.sidebar.multiselect("부서명", options=all_depts)
    sel_rank = st.sidebar.multiselect("직급 그룹", options=['실무자(사원/대리)', '관리자(차장↑)', '기타'])

    st.sidebar.markdown("---")
    st.sidebar.header("🚨 경고 알림 설정")
    warning_threshold = st.sidebar.number_input(
        "제안서 과다 다운로드 기준치", 
        min_value=1, value=10, step=1,
        help="설정하신 숫자 이상 제안서를 다운로드한 기록이 있는 경우 해당 셀을 붉은색으로 강조합니다."
    )

    # 필터링 적용
    def filter_df(df):
        if df.empty: return df
        res = df.copy()
        
        if 'date' in res.columns:
            if date_preset == "오늘":
                res = res[res['date'].dt.date == today]
            elif date_preset == "최근 1주일":
                default_start = today - timedelta(days=7)
                res = res[(res['date'].dt.date >= default_start) & (res['date'].dt.date <= today)]
            elif date_preset == "직접 지정" and date_range:
                if len(date_range) == 2:
                    res = res[(res['date'].dt.date >= date_range[0]) & (res['date'].dt.date <= date_range[1])]
                elif len(date_range) == 1:
                    res = res[res['date'].dt.date == date_range[0]]
            # "전체"인 경우 날짜 필터 생략
            
        if sel_dept and '부서' in res.columns: 
            res = res[res['부서'].isin(sel_dept)]
            
        if sel_rank:
            if '직급그룹' not in res.columns and '직급' in res.columns:
                res['직급그룹'] = res['직급'].apply(group_rank)
            if '직급그룹' in res.columns:
                res = res[res['직급그룹'].isin(sel_rank)]
                
        return res

    f_login = filter_df(df_login)
    f_download = filter_df(df_download)
    f_proposal = filter_df(df_proposal)

    # --- 4. 대시보드 UI ---
    st.title("📈 2026 통합 로그 분석 대시보드")

    # KPI 섹션
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("총 로그인수", f"{len(f_login)}건")
    c2.metric("제안서 다운로드", f"{len(f_proposal)}건")
    
    if not f_download.empty and '경로 메뉴명' in f_download.columns:
        c3.metric("프로젝트 찾기", f"{len(f_download[f_download['경로 메뉴명'].astype(str).str.contains('프로젝트', na=False)])}건")
        c4.metric("운영자료 찾기", f"{len(f_download[f_download['경로 메뉴명'].astype(str).str.contains('운영자료', na=False)])}건")
        c5.metric("서포트 센터", f"{len(f_download[f_download['경로 메뉴명'].astype(str).str.contains('서포트', na=False)])}건")
    else:
        c3.metric("프로젝트 찾기", "0건")
        c4.metric("운영자료 찾기", "0건")
        c5.metric("서포트 센터", "0건")

    # 그래프 섹션
    st.subheader("🗓️ 일자별 활동 현황")
    if not f_login.empty and 'date' in f_login.columns:
        daily_logs = f_login.groupby(f_login['date'].dt.date).size().reset_index(name='count')
        st.line_chart(daily_logs.set_index('date'))
    else:
        st.info("해당 조건의 로그인 데이터가 없거나 로그인 일자 컬럼을 찾을 수 없습니다.")

    # 직원별 상세 현황 및 모니터링 레이아웃 분할
    st.markdown("---")
    main_col1, main_col2 = st.columns(2)
    
    with main_col1:
        st.subheader("👤 직원별 활동 로그 상세")
        
        candidate_cols = ['UserNo', '이름', '부서', '직급']
        user_table = pd.DataFrame()
        login_cols = []
        
        if not f_login.empty:
            login_cols = [col for col in candidate_cols if col in f_login.columns]
            if login_cols:
                user_table = f_login.groupby(login_cols).size().reset_index(name='로그인수')

        if not f_proposal.empty:
            prop_cols = [col for col in candidate_cols if col in f_proposal.columns]
            if prop_cols:
                prop_table = f_proposal.groupby(prop_cols).size().reset_index(name='제안서 다운로드수')
                if not user_table.empty:
                    common_cols = list(set(login_cols).intersection(set(prop_cols)))
                    if common_cols:
                        user_table = pd.merge(user_table, prop_table, on=common_cols, how='outer')
                else:
                    user_table = prop_table
                    user_table['로그인수'] = 0

        if not user_table.empty:
            if '로그인수' not in user_table.columns:
                user_table['로그인수'] = 0
            if '제안서 다운로드수' not in user_table.columns:
                user_table['제안서 다운로드수'] = 0
                
            user_table['로그인수'] = user_table['로그인수'].fillna(0).astype(int)
            user_table['제안서 다운로드수'] = user_table['제안서 다운로드수'].fillna(0).astype(int)
            user_table['합계'] = user_table['로그인수'] + user_table['제안서 다운로드수']
            
            user_table = user_table.sort_values(by='합계', ascending=False)
            display_df = user_table.drop(columns=['합계'])
            
            # 설정된 과다 다운로드 기준치를 넘는 경우 해당 컬럼만 하이라이팅
            def highlight_warning(row):
                styles = [''] * len(row)
                if row.get('제안서 다운로드수', 0) >= warning_threshold:
                    col_idx = display_df.columns.get_loc('제안서 다운로드수')
                    styles[col_idx] = 'background-color: rgba(255, 75, 75, 0.15); color: #ff4b4b; font-weight: bold'
                return styles

            st.dataframe(display_df.style.apply(highlight_warning, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("상세 로그 데이터가 없습니다.")

    with main_col2:
        st.subheader("🕵️ 단기간 제안서 과다 다운로더 모니터링")
        
        if not user_table.empty:
            show_heavy_downloader = st.checkbox(f"제안서 기준치({warning_threshold}건 이상) 경고 사용자 심층 분석 보기", value=True)
            
            if show_heavy_downloader:
                warned_users = user_table[user_table['제안서 다운로드수'] >= warning_threshold]['이름'].tolist()
                if not warned_users:
                    st.success("현재 기준치 이상 제안서를 다운로드한 사용자가 없습니다.")
                else:
                    st.warning(f"총 {len(warned_users)}명의 경고 대상자가 발견되었습니다.")
                    heavy_logs = f_proposal[f_proposal['이름'].isin(warned_users)].copy()
                    
                    if not heavy_logs.empty:
                        # '파일제목' 대신 '문서경로' 컬럼 사용
                        doc_col = '문서경로' if '문서경로' in heavy_logs.columns else '비고'
                        unique_counts = heavy_logs.groupby(['UserNo', '이름', '부서', '직급'])[doc_col].nunique().reset_index(name='열람한 고유 파일 개수')
                        
                        sort_col = '제안서 다운로드 일시' if '제안서 다운로드 일시' in heavy_logs.columns else 'date'
                        timeline_cols = ['date', '이름', '부서', doc_col]
                        if sort_col not in timeline_cols:
                            timeline_cols.append(sort_col)
                        
                        timeline_df = heavy_logs[timeline_cols].copy()
                        timeline_df = timeline_df.sort_values(by=['이름', sort_col], ascending=[True, False])
                        timeline_df = timeline_df.rename(columns={doc_col: '조회 문서'})
                        
                        st.markdown("##### 📍 다운로드 의심 여부 (고유 조회 수)")
                        st.caption("총 다운로드 수 대비 여러 개의 제안서를 넓게 볼수록(쇼핑) 위험도가 높습니다.")
                        
                        def highlight_unique(row):
                            val = row.get('열람한 고유 파일 개수', 0)
                            if val >= warning_threshold:
                                return ['background-color: #ffcccc; color: #cc0000; font-weight:bold'] * len(row)
                            elif val >= warning_threshold / 2:
                                return ['background-color: #ffe6e6; color: #880000'] * len(row)
                            return [''] * len(row)
                                
                        st.dataframe(unique_counts.style.apply(highlight_unique, axis=1), hide_index=True, use_container_width=True)
                        
                        st.markdown("##### 🕒 개별 다운로드 타임라인")
                        st.caption("어떤 파일을 이어서 보았는지 분석합니다.")
                        st.dataframe(timeline_df, hide_index=True, use_container_width=True)
                    else:
                        st.info("조건에 맞는 제안서 상세 기록을 불러올 수 없습니다.")
        else:
             st.info("비교할 데이터가 없습니다.")

except FileNotFoundError:
    st.error("`.streamlit/secrets.toml` 파일에 GCP 인증 정보가 설정되지 않았거나 파일을 찾을 수 없습니다. 설정 후에 다시 시도해주세요.")
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("Google Sheet API 연동, 시트 권한, 혹은 존재하지 않는 시트 탭이 있는지 확인해 주세요.")

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import config

# --- [load 블록] ---

@st.cache_data(ttl=600)
def load_all():
    """
    Google Sheets에서 모든 데이터를 원본 그대로 로드하고,
    직원정보의 병합 헤더를 평탄화합니다.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 1. Streamlit Secrets 확인 (대시보드 실행 시)
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
            sheet_url = st.secrets["gcp_sheet_url"]
        else:
            # 2. 로컬 JSON 키 파일 확인 (스케줄러 등 일반 실행 시)
            # collector.py와 동일한 경로 사용
            json_path = r"C:\김연아\@ AXDX팀\1. 로그인, 다운로드 대시보드 제작\@micedx1계정api키정보\ezdatahub-log-5a89069d212c.json"
            creds = Credentials.from_service_account_file(json_path, scopes=scope)
            sheet_url = "https://docs.google.com/spreadsheets/d/1N0UUF2Qroqbukd37WRgur2FpjzxEXLevT79EB_GutEk/edit?usp=sharing"
        
        client = gspread.authorize(creds)
        sh = client.open_by_url(sheet_url)
    except Exception as e:
        print(f"Google Sheets 연결 실패: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    def get_df_safe(sheet_name):
        try:
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_values()
            if not data:
                return pd.DataFrame()
            
            # 중복 컬럼명 처리
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
            # 숫자 자동 변환
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass
            return df
        except gspread.exceptions.WorksheetNotFound:
            return pd.DataFrame()

    # 일반 로그 시트 로드
    df_login = get_df_safe(config.SHEET_NAME_LOGIN)
    df_download = get_df_safe(config.SHEET_NAME_DOWNLOAD)
    df_proposal = get_df_safe(config.SHEET_NAME_PROPOSAL)

    # 직원정보 시트 헤더 평탄화
    df_users = pd.DataFrame()
    try:
        ws_users = sh.worksheet(config.SHEET_NAME_USERS)
        raw_users = ws_users.get_all_values()
        if len(raw_users) >= 2:
            row0 = raw_users[0]  # 연도 행
            row1 = raw_users[1]  # 컬럼명 행
            
            # forward fill for years
            current_year_val = ""
            flattened_headers = []
            # 고정 컬럼에서 config.COL_NAME_EMAIL(PRS ID) 사용
            fixed_cols = ["UserNo", "임직원명", config.COL_NAME_EMAIL, "입사일자"]
            
            for y, c in zip(row0, row1):
                y_str = str(y).strip()
                c_str = str(c).strip()
                
                if y_str:
                    current_year_val = y_str
                
                if c_str in fixed_cols or not current_year_val:
                    flattened_headers.append(c_str)
                else:
                    flattened_headers.append(f"{current_year_val}_{c_str}")
            
            df_users = pd.DataFrame(raw_users[2:], columns=flattened_headers)
            # No 컬럼 제외
            if "No" in df_users.columns:
                df_users = df_users.drop(columns=["No"])
            # [수정] 부서명 공란 필터링 제거 (모든 인원 유지 - 과거 데이터 조인용)
            # df_users = df_users[df_users[curr_dept_col].astype(str).str.strip() != ""]
    except Exception as e:
        st.warning(f"직원정보 로드 실패: {e}")

    return df_users, df_login, df_download, df_proposal

# --- [map 블록] ---

def map_all(df_users, df_login, df_download, df_proposal):
    """
    UserNo 정규화, 이메일 매핑, 마스터 정보 조인을 수행합니다.
    """
    if df_users.empty:
        return df_users, df_login, df_download, df_proposal

    # 1. UserNo 정규화 (3자리 zero-padding)
    def normalize_userno(val):
        if pd.isna(val) or str(val).strip() == "" or str(val).lower() == 'nan':
            return ""
        # 소수점 제거 및 공백 제거
        s = str(val).strip().replace('.0', '')
        # 숫자인 경우 3자리 자릿수 맞춤
        if s.isdigit():
            return s.zfill(3)
        return s

    if 'UserNo' in df_users.columns:
        df_users['UserNo'] = df_users['UserNo'].apply(normalize_userno)

    # 2. PRS ID -> UserNo 역매핑 브릿지 (직원정보 마스터 활용)
    email_to_userno = {}
    if config.COL_NAME_EMAIL in df_users.columns:
        email_to_userno = df_users[df_users[config.COL_NAME_EMAIL].str.strip() != ""].set_index(config.COL_NAME_EMAIL)['UserNo'].to_dict()

    # 3. 각 시트 조인 처리
    def join_master_info(df, master):
        if df.empty: return df
        df = df.copy()
        
        # UserNo 정규화
        u_col = 'userNo' if 'userNo' in df.columns else 'UserNo' if 'UserNo' in df.columns else None
        if u_col:
            df[u_col] = df[u_col].apply(normalize_userno)
        
        # PRS ID (이메일) 컬럼이 있고 UserNo가 없는 경우 매핑 (제안서 등)
        if config.COL_NAME_EMAIL in df.columns and (not u_col or (df[u_col] == "").all()):
            df[config.COL_NAME_EMAIL] = df[config.COL_NAME_EMAIL].astype(str).str.strip()
            df['UserNo_mapped'] = df[config.COL_NAME_EMAIL].map(email_to_userno)
            u_col = 'UserNo_mapped'
        
        if not u_col: return df

        # 기존 이름/부서/직급 등 컬럼 삭제
        cols_to_drop = [c for c in ['이름', '부서', '직급', '부서명', '직급그룹'] if c in df.columns]
        df.drop(columns=cols_to_drop, inplace=True)

        # 마스터 조인 (UserNo 기준)
        # 양쪽 UserNo 컬럼 정규화 (유저 요청 스펙 반영)
        df[u_col] = df[u_col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(3)
        master['UserNo'] = master['UserNo'].astype(str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(3)
        
        # 중복 컬럼 확인 (디버깅)
        # print("df 중복 컬럼:", df.columns[df.columns.duplicated()].tolist())
        # print("master 중복 컬럼:", master.columns[master.columns.duplicated()].tolist())

        # 중복 컬럼 제거 후 merge
        df = df.loc[:, ~df.columns.duplicated()]
        master = master.loc[:, ~master.columns.duplicated()]
        master = master.drop_duplicates(subset=['UserNo'], keep='first')
        
        df = pd.merge(df, master, left_on=u_col, right_on='UserNo', how='left', suffixes=('', '_master'))
        
        # merge로 생긴 중복 컬럼 제거
        master_cols = [c for c in df.columns if c.endswith('_master')]
        df = df.drop(columns=master_cols)
        df = df.reset_index(drop=True)

        # 연도별 정보 적용 (부서명 Fallback 포함)
        def apply_year_info(row):
            # year가 없거나 유효하지 않으면 CURRENT_YEAR 사용
            try:
                y = row.get('year')
                if pd.isna(y) or y == 0:
                    y_str = str(config.CURRENT_YEAR)
                else:
                    y_str = str(int(y))
            except:
                y_str = str(config.CURRENT_YEAR)
            
            dept_col = config.YEAR_COL_DEPT.format(year=y_str)
            hq_col = config.YEAR_COL_HQ.format(year=y_str)
            rank_col = config.YEAR_COL_RANK.format(year=y_str)
            div_col = config.YEAR_COL_DIVISION.format(year=y_str)
            
            # 부서명 Fallback: 부서명(Dept) -> 본부/실(HQ) -> 사업부(Division)
            # 1. 1차: 해당 연도 부서명
            dept_val = row.get(dept_col)
            
            # 2. 2차: 해당 연도 본부/실
            if pd.isna(dept_val) or str(dept_val).strip() == "":
                dept_val = row.get(hq_col)
            
            # 3. 3차: 해당 연도 사업부
            if pd.isna(dept_val) or str(dept_val).strip() == "":
                dept_val = row.get(div_col)

            # 4. 4차: 최후의 수단으로 '정보미등록' (UI에서 처리하므로 일단 유지)
            
            # 4. 부서별 현황 페이지 전용 커스텀 그룹핑 (부서_그룹)
            # 기준: 특정 본부명(config.DEPT_SHOW_AS_HQ)이면 본부명, 그 외는 사업부명 (사업부 없으면 본부)
            hq_val = str(row.get(hq_col, "")).strip()
            div_val = str(row.get(div_col, "")).strip()
            
            if hq_val in config.DEPT_SHOW_AS_HQ:
                row['부서_그룹'] = hq_val
            elif div_val:
                row['부서_그룹'] = div_val
            else:
                row['부서_그룹'] = hq_val if hq_val else "M-Level"
            
            row['이름'] = row.get('임직원명', "")
            row['부서'] = str(dept_val).strip() if not pd.isna(dept_val) else ""
            row['직급'] = str(row.get(rank_col, "")).strip()
            return row

        df = df.apply(apply_year_info, axis=1)
        return df

    df_login = join_master_info(df_login, df_users)
    df_download = join_master_info(df_download, df_users)
    df_proposal = join_master_info(df_proposal, df_users)

    # 4. 마스터(df_users) 자체에도 현재 연도 기준 표준 컬럼 추가
    if not df_users.empty:
        # df_users는 이미 마스터이므로 조인 대신 직접 apply_year_info와 유사하게 가공
        # year 컬럼이 없으므로 CURRENT_YEAR를 강제 적용하여 부서/직급 생성
        df_users['year'] = config.CURRENT_YEAR
        
        # dummy join_master_info 효과를 위해 apply_year_info 내부 로직 직접 호출 (또는 dummy join)
        # 여기서는 단순히 apply_year_info와 같은 로직을 로컬 함수로 정의하여 적용
        def prepare_master(row):
            y_str = str(config.CURRENT_YEAR)
            dept_col = config.YEAR_COL_DEPT.format(year=y_str)
            hq_col = config.YEAR_COL_HQ.format(year=y_str)
            div_col = config.YEAR_COL_DIVISION.format(year=y_str)
            rank_col = config.YEAR_COL_RANK.format(year=y_str)
            
            dept_val = row.get(dept_col)
            if pd.isna(dept_val) or str(dept_val).strip() == "":
                dept_val = row.get(hq_col)
            if pd.isna(dept_val) or str(dept_val).strip() == "":
                dept_val = row.get(div_col)
            
            row['이름'] = row.get('임직원명', "")
            row['부서'] = str(dept_val).strip() if not pd.isna(dept_val) else ""
            row['직급'] = str(row.get(rank_col, "")).strip()
            
            # [추가] 부서별 현황 페이지용 그룹핑
            hq_val = str(row.get(hq_col, "")).strip()
            div_val = str(row.get(div_col, "")).strip()
            if hq_val in config.DEPT_SHOW_AS_HQ:
                row['부서_그룹'] = hq_val
            elif div_val:
                row['부서_그룹'] = div_val
            else:
                row['부서_그룹'] = hq_val if hq_val else "M-Level"
                
            row['_ui_dept'] = row['부서'] if row['부서'] else "M-Level"
            return row
            
        df_users = df_users.apply(prepare_master, axis=1)

    return df_users, df_login, df_download, df_proposal

# --- [preprocess 블록] ---

def preprocess_all(df_users, df_login, df_download, df_proposal):
    """
    날짜 통일, 연도 추출, 직급 그룹화를 수행합니다.
    """
    def process_df(df):
        if df.empty: return df
        df = df.copy()
        
        # 1. 날짜 및 시간 컬럼 통합 (정밀한 구간 필터링용)
        date_time_pairs = [
            ('다운로드 일자', '다운로드 시간'),
            ('로그인 일자', '로그인 시간'),
            ('등록일', '등록시간') # 제안서 등 기타 시트 대비
        ]
        
        for d_col, t_col in date_time_pairs:
            if d_col in df.columns:
                if t_col in df.columns:
                    # 날짜와 시간을 합쳐서 pandas datetime 객체로 변환
                    df['date'] = pd.to_datetime(df[d_col].astype(str) + ' ' + df[t_col].astype(str), errors='coerce')
                else:
                    df['date'] = pd.to_datetime(df[d_col], errors='coerce')
                break
        
        if 'date' in df.columns:
            # 2. year 컬럼 추가
            df['year'] = df['date'].dt.year
            
        return df

    df_login = process_df(df_login)
    df_download = process_df(df_download)
    df_proposal = process_df(df_proposal)

    return df_users, df_login, df_download, df_proposal

def add_rank_group(df):
    if df.empty or '직급' not in df.columns: return df
    def group_rank(rank):
        if pd.isna(rank): return '기타'
        rank_str = str(rank).strip()
        if rank_str in ['사원', '대리']: return '실무자(사원/대리)'
        if rank_str in ['차장', '팀장', '부장', '본부장']: return '관리자(차장↑)'
        if rank_str in ['임원']: return '임원'
        return '기타'
    df['직급그룹'] = df['직급'].apply(group_rank)
    return df

def run_all():
    """
    데이터 로드부터 전처리까지 전체 프로세스를 실행합니다.
    """
    df_users, df_login, df_download, df_proposal = load_all()
    
    # [기본 제외 대상 제거] 테스트 계정 및 특정 유저 (config.DEFAULT_EXCLUDE_USERNO)
    def exclude_users(df):
        if df.empty or 'UserNo' not in df.columns: return df
        # 정규화하여 비교
        def norm(s): return str(s).strip().replace('.0', '').zfill(3)
        excluded_norm = [norm(u) for u in config.DEFAULT_EXCLUDE_USERNO]
        # 기존 테스트 계정 556도 함께 체크
        excluded_norm.append('556')
        
        return df[~df['UserNo'].apply(norm).isin(excluded_norm)]

    df_users = exclude_users(df_users)
    df_login = exclude_users(df_login)
    df_download = exclude_users(df_download)
    df_proposal = exclude_users(df_proposal)
    
    # Preprocess (날짜/연도 추출)
    df_users, df_login, df_download, df_proposal = preprocess_all(df_users, df_login, df_download, df_proposal)
    
    # Map (연도 기반 조인 & Fallback)
    df_users, df_login, df_download, df_proposal = map_all(df_users, df_login, df_download, df_proposal)
    
    # Post-process (직급 그룹화)
    df_users = add_rank_group(df_users)
    df_login = add_rank_group(df_login)
    df_download = add_rank_group(df_download)
    df_proposal = add_rank_group(df_proposal)

    return df_users, df_login, df_download, df_proposal

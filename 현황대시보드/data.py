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
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sh = client.open_by_url(st.secrets["gcp_sheet_url"])
    except Exception as e:
        st.error(f"Google Sheets 연결 실패: {e}")
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
            # 퇴사자 판별 (CURRENT_YEAR 기준 부서명이 빈칸이면 제외)
            curr_dept_col = config.YEAR_COL_DEPT.format(year=config.CURRENT_YEAR)
            if curr_dept_col in df_users.columns:
                df_users = df_users[df_users[curr_dept_col].astype(str).str.strip() != ""]
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
        s = str(val).strip().replace('.0', '')
        return s.zfill(3) if s and s != 'nan' else ""

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
            y = row.get('year')
            if pd.isna(y): return row
            
            y_str = str(int(y))
            dept_col = config.YEAR_COL_DEPT.format(year=y_str)
            hq_col = config.YEAR_COL_HQ.format(year=y_str)
            rank_col = config.YEAR_COL_RANK.format(year=y_str)
            
            # 부서명 Fallback: 부서명 없으면 본부/실
            dept_val = row.get(dept_col)
            if pd.isna(dept_val) or str(dept_val).strip() == "":
                dept_val = row.get(hq_col)
            
            row['이름'] = row.get('임직원명', "")
            row['부서'] = dept_val
            row['직급'] = row.get(rank_col, "")
            return row

        df = df.apply(apply_year_info, axis=1)
        return df

    df_login = join_master_info(df_login, df_users)
    df_download = join_master_info(df_download, df_users)
    df_proposal = join_master_info(df_proposal, df_users)

    return df_users, df_login, df_download, df_proposal

# --- [preprocess 블록] ---

def preprocess_all(df_users, df_login, df_download, df_proposal):
    """
    날짜 통일, 연도 추출, 직급 그룹화를 수행합니다.
    """
    def process_df(df):
        if df.empty: return df
        df = df.copy()
        
        # 1. 날짜 컬럼 통일
        for date_col in ['등록일', '다운로드 일자', '로그인 일자']:
            if date_col in df.columns:
                df['date'] = pd.to_datetime(df[date_col], errors='coerce')
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
        if rank_str in ['사원', '대리', '주임', '연구원']: return '실무자(사원/대리)'
        if rank_str in ['차장', '팀장', '부장', '본부장', '이사', '실장', '수석', '상무', '전무']: return '관리자(차장↑)'
        return '기타'
    df['직급그룹'] = df['직급'].apply(group_rank)
    return df

def run_all():
    """
    데이터 로드부터 전처리까지 전체 프로세스를 실행합니다.
    """
    df_users, df_login, df_download, df_proposal = load_all()
    
    # Preprocess (날짜/연도 추출)
    df_users, df_login, df_download, df_proposal = preprocess_all(df_users, df_login, df_download, df_proposal)
    
    # Map (연도 기반 조인 & Fallback)
    df_users, df_login, df_download, df_proposal = map_all(df_users, df_login, df_download, df_proposal)
    
    # Post-process (직급 그룹화)
    df_login = add_rank_group(df_login)
    df_download = add_rank_group(df_download)
    df_proposal = add_rank_group(df_proposal)

    return df_users, df_login, df_download, df_proposal

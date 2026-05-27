import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import config

# --- [load 블록] ---

@st.cache_data(ttl=600)
def load_from_api():
    """
    사내 REST API에서 모든 데이터를 로드하고 DataFrame으로 반환합니다.
    """
    import requests
    
    headers = getattr(config, "API_HEADERS", {})
    endpoints = getattr(config, "API_ENDPOINTS", {})
    
    def fetch_df(api_key):
        url = endpoints.get(api_key)
        if not url:
            return pd.DataFrame()
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                json_data = response.json()
                if isinstance(json_data, dict) and 'data' in json_data:
                    data_list = json_data['data']
                elif isinstance(json_data, list):
                    data_list = json_data
                else:
                    data_list = []
                
                df = pd.DataFrame(data_list)
                
                # PK 컬럼 중복 제거
                pk_cols = ['NO', 'No', '번호']
                actual_pk = [c for c in pk_cols if c in df.columns]
                if actual_pk:
                    df = df.drop_duplicates(subset=actual_pk, keep='last')
                
                # 숫자 자동 변환
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except (ValueError, TypeError):
                        pass
                return df
            else:
                st.warning(f"API {api_key} 호출 실패 (Status: {response.status_code})")
                return pd.DataFrame()
        except Exception as e:
            st.warning(f"API {api_key} 연결 실패: {e}")
            return pd.DataFrame()

    df_users = fetch_df("users")
    df_login = fetch_df("login")
    df_download = fetch_df("download")
    df_proposal = fetch_df("proposal")
    
    # 만약 직원정보에 No 컬럼이 들어있다면 제거
    if "No" in df_users.columns:
        df_users = df_users.drop(columns=["No"])
        
    return df_users, df_login, df_download, df_proposal

@st.cache_data(ttl=600)
def load_all():
    """
    설정된 소스 모드(DATA_SOURCE_MODE)에 따라 데이터를 로드합니다.
    Google Sheets 또는 REST API에서 모든 데이터를 원본 그대로 로드하고,
    직원정보의 병합 헤더를 평탄화합니다.
    """
    mode = getattr(config, "DATA_SOURCE_MODE", "GSPREAD")
    if mode == "REST_API":
        return load_from_api()
        
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 1. Streamlit Secrets 확인 (대시보드 실행 시)
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
            sheet_url = st.secrets["gcp_sheet_url"]
        else:
            # 2. 로컬 secrets.toml 직접 로드 (스케줄러/배치 등 일반 실행 시)
            import os
            import tomllib
            secrets_path = os.path.join(".streamlit", "secrets.toml")
            if not os.path.exists(secrets_path):
                raise FileNotFoundError(f"인증 정보 파일을 찾을 수 없습니다: {secrets_path}")
                
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
                creds = Credentials.from_service_account_info(secrets["gcp_service_account"], scopes=scope)
                sheet_url = secrets.get("gcp_sheet_url", "https://docs.google.com/spreadsheets/d/1N0UUF2Qroqbukd37WRgur2FpjzxEXLevT79EB_GutEk/edit?usp=sharing")
        
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
            
            # [추가] 고유 번호 기반 중복 제거 (방어 로직)
            pk_cols = ['NO', 'No', '번호']
            actual_pk = [c for c in pk_cols if c in df.columns]
            if actual_pk:
                df = df.drop_duplicates(subset=actual_pk, keep='last')
            
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
        # 이메일 앞뒤 공백 제거 및 소문자 통일하여 매핑 사전 생성
        temp_df = df_users.copy()
        temp_df[config.COL_NAME_EMAIL] = temp_df[config.COL_NAME_EMAIL].astype(str).str.strip().str.lower()
        email_to_userno = temp_df[temp_df[config.COL_NAME_EMAIL] != ""].set_index(config.COL_NAME_EMAIL)['UserNo'].to_dict()

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
            # 로그의 이메일도 동일하게 공백 제거 및 소문자 정규화 수행
            df[config.COL_NAME_EMAIL] = df[config.COL_NAME_EMAIL].astype(str).str.strip().str.lower()
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

        # [최적화] apply(axis=1) 루프 제거 및 벡터화 연산 일괄 처리
        if 'year' not in df.columns:
            df['year'] = config.CURRENT_YEAR
        else:
            df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(config.CURRENT_YEAR).astype(int)
            
        df['부서'] = ""
        df['사업부'] = "정보미등록"
        df['직급'] = ""
        df['부서_그룹'] = "M-Level"
        df['이름'] = df['임직원명'].fillna("").astype(str).str.strip() if '임직원명' in df.columns else ""

        unique_years = df['year'].unique()
        for y in unique_years:
            y_str = str(int(y))
            dept_col = config.YEAR_COL_DEPT.format(year=y_str)
            hq_col = config.YEAR_COL_HQ.format(year=y_str)
            div_col = config.YEAR_COL_DIVISION.format(year=y_str)
            rank_col = config.YEAR_COL_RANK.format(year=y_str)
            
            mask = df['year'] == y
            if not mask.any():
                continue
                
            # 1. 직급 매핑
            if rank_col in df.columns:
                df.loc[mask, '직급'] = df.loc[mask, rank_col].astype(str).str.strip().fillna("")
                
            # 2. 사업부 매핑
            if div_col in df.columns:
                div_series = df.loc[mask, div_col].astype(str).str.strip()
                df.loc[mask, '사업부'] = div_series.replace(['nan', 'NaN', ''], '정보미등록').fillna('정보미등록')
                
            # 3. 부서 Fallback 일괄 계산 (dept -> hq -> div)
            dept_val = df.loc[mask, dept_col].astype(str).str.strip().replace(['nan', 'NaN', ''], None) if dept_col in df.columns else pd.Series(None, index=df[mask].index)
            hq_val = df.loc[mask, hq_col].astype(str).str.strip().replace(['nan', 'NaN', ''], None) if hq_col in df.columns else pd.Series(None, index=df[mask].index)
            div_val = df.loc[mask, div_col].astype(str).str.strip().replace(['nan', 'NaN', ''], None) if div_col in df.columns else pd.Series(None, index=df[mask].index)
            
            fallback_dept = dept_val.combine_first(hq_val).combine_first(div_val).fillna("")
            df.loc[mask, '부서'] = fallback_dept
            
            # 4. 부서_그룹 일괄 계산
            hq_series = df.loc[mask, hq_col].astype(str).str.strip().fillna("") if hq_col in df.columns else pd.Series("", index=df[mask].index)
            div_series = df.loc[mask, div_col].astype(str).str.strip().fillna("") if div_col in df.columns else pd.Series("", index=df[mask].index)
            
            # CP실 / 주최사업실 등 본부명 유지
            hq_mask = hq_series.isin(config.DEPT_SHOW_AS_HQ)
            df.loc[mask & hq_mask, '부서_그룹'] = hq_series[hq_mask]
            
            # 그 외 사업부명 사용
            div_mask = (~hq_mask) & (div_series != "") & (div_series != "nan")
            df.loc[mask & div_mask, '부서_그룹'] = div_series[div_mask]
            
            # 둘 다 아닌 경우 본부명 fallback (없으면 M-Level)
            fallback_mask = (~hq_mask) & ((div_series == "") | (div_series == "nan"))
            df.loc[mask & fallback_mask, '부서_그룹'] = hq_series[fallback_mask].replace(['nan', ''], 'M-Level')

        return df

    df_login = join_master_info(df_login, df_users)
    df_download = join_master_info(df_download, df_users)
    df_proposal = join_master_info(df_proposal, df_users)

    # 4. 마스터(df_users) 자체에도 현재 연도 기준 표준 컬럼 추가 (apply 루프 제거)
    if not df_users.empty:
        y_str = str(config.CURRENT_YEAR)
        dept_col = config.YEAR_COL_DEPT.format(year=y_str)
        hq_col = config.YEAR_COL_HQ.format(year=y_str)
        div_col = config.YEAR_COL_DIVISION.format(year=y_str)
        rank_col = config.YEAR_COL_RANK.format(year=y_str)

        df_users['year'] = config.CURRENT_YEAR
        df_users['이름'] = df_users['임직원명'].fillna("").astype(str).str.strip()
        df_users['부서'] = ""
        df_users['사업부'] = "정보미등록"
        df_users['직급'] = ""
        df_users['부서_그룹'] = "M-Level"

        if rank_col in df_users.columns:
            df_users['직급'] = df_users[rank_col].astype(str).str.strip().fillna("")
            
        if div_col in df_users.columns:
            df_users['사업부'] = df_users[div_col].astype(str).str.strip().replace(['nan', 'NaN', ''], '정보미등록').fillna('정보미등록')

        dept_val = df_users[dept_col].astype(str).str.strip().replace(['nan', 'NaN', ''], None) if dept_col in df_users.columns else pd.Series(None, index=df_users.index)
        hq_val = df_users[hq_col].astype(str).str.strip().replace(['nan', 'NaN', ''], None) if hq_col in df_users.columns else pd.Series(None, index=df_users.index)
        div_val = df_users[div_col].astype(str).str.strip().replace(['nan', 'NaN', ''], None) if div_col in df_users.columns else pd.Series(None, index=df_users.index)
        
        df_users['부서'] = dept_val.combine_first(hq_val).combine_first(div_val).fillna("")

        hq_series = df_users[hq_col].astype(str).str.strip().fillna("") if hq_col in df_users.columns else pd.Series("", index=df_users.index)
        div_series = df_users[div_col].astype(str).str.strip().fillna("") if div_col in df_users.columns else pd.Series("", index=df_users.index)

        hq_mask = hq_series.isin(config.DEPT_SHOW_AS_HQ)
        df_users.loc[hq_mask, '부서_그룹'] = hq_series[hq_mask]

        div_mask = (~hq_mask) & (div_series != "") & (div_series != "nan")
        df_users.loc[div_mask, '부서_그룹'] = div_series[div_mask]

        fallback_mask = (~hq_mask) & ((div_series == "") | (div_series == "nan"))
        df_users.loc[fallback_mask, '부서_그룹'] = hq_series[fallback_mask].replace(['nan', ''], 'M-Level')
            
        df_users['_ui_dept'] = df_users['부서'].replace('', 'M-Level')

    return df_users, df_login, df_download, df_proposal

# --- [preprocess 블록] ---

def preprocess_all(df_users, df_login, df_download, df_proposal):
    """
    날짜 통일, 연도 추출, 직급 그룹화를 수행합니다.
    """
    def process_df(df):
        if df.empty: return df
        df = df.copy()
        
        # 1. 날짜 및 시간 컬럼 통합 (유효한 데이터가 있는 컬럼 우선 탐색)
        date_time_pairs = [
            ('등록일', '등록시간'),
            ('다운로드 일자', '다운로드 시간'),
            ('로그인 일자', '로그인 시간')
        ]
        
        best_date_series = None
        max_valid_dates = -1
        
        for d_col, t_col in date_time_pairs:
            if d_col in df.columns:
                if t_col in df.columns:
                    temp_date = pd.to_datetime(df[d_col].astype(str) + ' ' + df[t_col].astype(str), errors='coerce')
                else:
                    temp_date = pd.to_datetime(df[d_col], errors='coerce')
                
                valid_count = temp_date.notna().sum()
                if valid_count > max_valid_dates:
                    max_valid_dates = valid_count
                    best_date_series = temp_date
                
                # 모든 행이 유효하면 즉시 중단 (최적화)
                if valid_count == len(df):
                    break
        
        if best_date_series is not None:
            df['date'] = best_date_series
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

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config
import re

# --- [UI Style Helper: Metrics] ---
def render_metric_card(label, value, color="#6366f1"):
    st.markdown(f"""
    <div class="metric-card" style="text-align: center; border-left: 4px solid {color}; padding-left: 10px;">
        <div style="color: #64748b; font-size: 11px; font-weight: 600; text-transform: uppercase;">{label}</div>
        <div style="color: #1e293b; font-size: 20px; font-weight: 800;">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# --- [Page Header] ---
st.markdown(f"""
<div class="page-header" style="padding: 12px 24px; margin-bottom: 16px;">
    <div style="font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; opacity: 0.8;">Analysis</div>
    <div style="font-size: 24px; font-weight: 800; margin-bottom: 4px;"> {config.CURRENT_YEAR}년 EZ데이터허브 사용자 대시보드</div>
    <div style="font-size: 13px; opacity: 0.85; font-weight: 400;">{config.CURRENT_YEAR}년 EZ데이터허브 사용자의 파일 다운로드 현황을 확인할 수 있습니다.</div>
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
    elif sel_dept and '_ui_dept' in res.columns: # df_users용
        res = res[res['_ui_dept'].isin(sel_dept)]
    
    if sel_rank and '직급그룹' in res.columns:
        res = res[res['직급그룹'].isin(sel_rank)]
    return res

f_login = filter_data(df_login)
f_download = filter_data(df_download)
f_proposal = filter_data(df_proposal)
f_u = filter_data(df_u)

# [수치 정합성] 
for df in [f_login, f_download, f_proposal, f_u]:
    if not df.empty:
        # data.py에서 제공하는 표준 컬럼 사용 및 결측치 최종 보원
        if '부서' in df.columns: 
            df['부서'] = df['부서'].replace(['', None, 'nan', 'NaN'], '정보미등록').fillna('정보미등록')
        if '직급' in df.columns: 
            df['직급'] = df['직급'].replace(['', None, 'nan', 'NaN'], '정보미등록').fillna('정보미등록')
        if '직급그룹' in df.columns: 
            df['직급그룹'] = df['직급그룹'].replace(['', None, 'nan', 'NaN'], '정보미등록').fillna('정보미등록')

# --- 4. 섹션 1: 직원별 활동 상세내역 & 고유파일 열람 현황 ---
col_s1_left, col_s1_right = st.columns([3, 1])

# 고정 유저 데이터 (f_u 기준)
# data.py에서 이미 '이름', '부서', '직급'이 표준화됨
user_base = f_u[['UserNo', '이름', '부서', '직급']].copy()

# 활동 집계
login_agg = f_login.groupby('UserNo').size().reset_index(name='총로그인수')
proposal_agg = f_proposal.groupby('UserNo').size().reset_index(name='제안서다운로드')

def get_cat_agg(df, pattern, col_name):
    if df.empty: return pd.DataFrame(columns=['UserNo', col_name])
    temp = df[df['경로 메뉴명'].astype(str).str.contains(pattern, na=False)]
    return temp.groupby('UserNo').size().reset_index(name=col_name)

proj_agg = get_cat_agg(f_download, '프로젝트 찾기', '프로젝트찾기')
ops_agg = get_cat_agg(f_download, '운영자료 찾기', '운영자료 찾기')
supp_agg = get_cat_agg(f_download, '서포트 센터', '서포트센터')

# 통합 테이블 생성
df_user_activity = user_base.merge(login_agg, on='UserNo', how='left') \
                            .merge(proposal_agg, on='UserNo', how='left') \
                            .merge(proj_agg, on='UserNo', how='left') \
                            .merge(ops_agg, on='UserNo', how='left') \
                            .merge(supp_agg, on='UserNo', how='left') \
                            .fillna(0)

# 숫자형 변환
count_cols = ['총로그인수', '제안서다운로드', '프로젝트찾기', '운영자료 찾기', '서포트센터']
for c in count_cols:
    df_user_activity[c] = df_user_activity[c].astype(int)

with col_s1_left:
    st.markdown("##### 👤 직원별 활동 상세내역")
    # 조건부 서식 적용 (변경: 제안서 다운로드 컬럼에만 빨간색 표시)
    def highlight_proposal(val):
        color = '#ef4444' if isinstance(val, (int, float)) and val >= 10 else ''
        background = '#fee2e2' if color else ''
        return f'color: {color}; background-color: {background}; font-weight: bold;' if color else ''

    styled_activity = df_user_activity.sort_values('총로그인수', ascending=False).style.applymap(
        highlight_proposal, subset=['제안서다운로드']
    )
    st.dataframe(styled_activity, use_container_width=True, hide_index=True, height=300)

with col_s1_right:
    st.markdown("<div style='text-align: right; font-size: 11px; color: #64748b; margin-top: -25px;'>모니터링 기준 설정</div>", unsafe_allow_html=True)
    # 워닝 횟수 필터를 드롭다운(selectbox)으로 변경
    warning_threshold = st.selectbox(
        "제안서 워닝 횟수 설정", 
        options=[5, 10, 15, 20, 30, 50, 100], 
        index=1,
        key='user_page_threshold_v2'
    )
    st.session_state['warning_threshold'] = warning_threshold

    st.markdown("##### 🚨 고유파일 열람 현황")
    
    heavy_users = df_user_activity[df_user_activity['제안서다운로드'] >= warning_threshold].copy()
    st.markdown(f"<div style='font-size: 12px; margin-bottom: 8px;'>현재 필터 조건에서 총 <b style='color: #ef4444;'>{len(heavy_users)}</b>명의 사용자가 기준치({warning_threshold}건)를 초과했습니다.</div>", unsafe_allow_html=True)
    
    if not heavy_users.empty:
        selected_user = st.selectbox("기준치 초과 직원 리스트", 
                                     options=['전체 보기'] + heavy_users['이름'].tolist(),
                                     help="리스트 행을 선택하면 다운로드 타임라인에 그 선택직원 분석")
    else:
        st.success("기준치를 초과하는 직원이 없습니다.")
        selected_user = '전체 보기'

st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

# --- 5. 섹션 2: 다운로드 타임라인 ---
# 헤더와 필터를 한 행에 배치하여 우측 정렬 효과
col_t_title, col_t_filter = st.columns([3, 1])
with col_t_title:
    st.markdown("##### 🕒 다운로드 타임라인")
with col_t_filter:
    # 시간 단위를 드롭다운(selectbox)으로 설정 (변경: 1시간 ~ 24시간)
    time_options = ["로그 시간"] + [f"{i}시간" for i in range(1, 25)]
    time_unit = st.selectbox("시간 단위", options=time_options, index=0, label_visibility="collapsed")

# 타임라인 데이터 준비 (제안서 기준)
tl_data = f_proposal.copy()

if selected_user != '전체 보기':
    tl_data = tl_data[tl_data['이름'] == selected_user]

if not tl_data.empty:
    # 컬럼 정리: UserNo|이름|부서|직급|PRS ID|제안서 다운로드 수|문서이름|열람시간
    tl_display = tl_data[['UserNo', '이름', '부서', '직급', config.COL_NAME_EMAIL, '문서경로', 'date']].copy()
    tl_display.rename(columns={'문서경로': '문서이름', 'date': '열람시간'}, inplace=True)
    tl_display['제안서 다운로드 수'] = 1
    
    if "시간" in time_unit and time_unit != "로그 시간":
        try:
            h_val = int(time_unit.replace("시간", ""))
            tl_display['열람시간'] = tl_display['열람시간'].dt.floor(f'{h_val}H')
        except:
            pass
    
    # 열람시간 포맷
    tl_display['열람시간'] = tl_display['열람시간'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 순서 조정
    cols = ['UserNo', '이름', '부서', '직급', config.COL_NAME_EMAIL, '제안서 다운로드 수', '문서이름', '열람시간']
    st.dataframe(tl_display[cols].sort_values('열람시간', ascending=False), use_container_width=True, hide_index=True, height=250)
else:
    st.info("해당하는 다운로드 기록이 없습니다.")

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# --- 6. 섹션 3: 다운로드 현황 (Top 7 / Top 10) ---
st.markdown("##### 📊 다운로드 현황")
c1, c2, c3, c4 = st.columns(4)
table_height = 280  # 높이 동일하게 조절

with c1:
    st.markdown("###### 📂 제안서 top10")
    if not f_proposal.empty:
        def parse_project(path):
            match = re.search(r'/(\d{6})\[([^\]]+)\]', str(path))
            if match:
                return match.group(1), match.group(2)
            return None, None
        
        proj_info = f_proposal['문서경로'].apply(parse_project).apply(pd.Series)
        proj_info.columns = ['프로젝트 코드', '프로젝트명']
        top10_proj = proj_info.dropna().groupby(['프로젝트 코드', '프로젝트명']).size().reset_index(name='횟수')
        top10_proj = top10_proj.sort_values('횟수', ascending=False).head(10) # 다시 Top 10으로 복구
        st.dataframe(top10_proj, use_container_width=True, hide_index=True, height=table_height)
    else: st.info("데이터 없음")

with c2:
    st.markdown("###### 🔎 프로젝트 찾기 top10")
    proj_logs = f_download[f_download['경로 메뉴명'].astype(str).str.contains('프로젝트 찾기', na=False)]
    if not proj_logs.empty:
        if '파일명' not in proj_logs.columns:
            proj_logs['파일명'] = proj_logs['경로 메뉴명'].apply(lambda x: str(x).split('/')[-1])
        
        top10_p = proj_logs.groupby('파일명').size().reset_index(name='횟수')
        top10_p.columns = ['파일명', '횟수']
        top10_p = top10_p.sort_values('횟수', ascending=False).head(10)
        st.dataframe(top10_p, use_container_width=True, hide_index=True, height=table_height)
    else: st.info("데이터 없음")

with c3:
    st.markdown("###### 🛠️ 운영자료 찾기 top10")
    ops_logs = f_download[f_download['경로 메뉴명'].astype(str).str.contains('운영자료 찾기', na=False)]
    if not ops_logs.empty:
        if '파일명' not in ops_logs.columns:
            ops_logs['파일명'] = ops_logs['경로 메뉴명'].apply(lambda x: str(x).split('/')[-1])
        
        top10_ops = ops_logs.groupby('파일명').size().reset_index(name='횟수')
        top10_ops.columns = ['파일명', '횟수']
        top10_ops = top10_ops.sort_values('횟수', ascending=False).head(10)
        st.dataframe(top10_ops, use_container_width=True, hide_index=True, height=table_height)
    else: st.info("데이터 없음")

with c4:
    st.markdown("###### ☎️ 서포트 센터 top10")
    supp_logs = f_download[f_download['경로 메뉴명'].astype(str).str.contains('서포트 센터', na=False)]
    if not supp_logs.empty:
        if '파일명' not in supp_logs.columns:
            supp_logs['파일명'] = supp_logs['경로 메뉴명'].apply(lambda x: str(x).split('/')[-1])
        
        top10_supp = supp_logs.groupby('파일명').size().reset_index(name='횟수')
        top10_supp.columns = ['파일명', '횟수']
        top10_supp = top10_supp.sort_values('횟수', ascending=False).head(10)
        st.dataframe(top10_supp, use_container_width=True, hide_index=True, height=table_height)
    else: st.info("데이터 없음")

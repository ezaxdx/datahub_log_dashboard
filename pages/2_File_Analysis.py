import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config
import re

# --- [Page Header] ---
st.markdown(f"""
<div class="page-header">
    <div style="font-size: 10px; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-family: 'Inter';">Data Deep-dive</div>
    <div style="font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 4px; font-family: 'Manrope';">{config.CURRENT_YEAR} EZ데이터허브 파일 다운로드 현황</div>
    <div style="font-size: 14px; color: #64748b; font-weight: 400; font-family: 'Inter';">파일 다운로드 및 직원별 활동 내역을 심층 분석합니다.</div>
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
            elif len(date_range) == 1:
                res = res[res['date'].dt.date >= date_range[0]]
    if sel_dept and '부서' in res.columns:
        res = res[res['부서'].isin(sel_dept)]
    
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

# --- 4. 섹션 1: 직원별 활동 상세내역 & 제안서 다운로드 현황 ---
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
perf_agg = get_cat_agg(f_download, '프로젝트 실적', '프로젝트실적')
ops_agg = get_cat_agg(f_download, '운영자료 찾기', '운영자료 찾기')
supp_agg = get_cat_agg(f_download, '서포트 센터', '서포트센터')

# 통합 테이블 생성
df_user_activity = user_base.merge(login_agg, on='UserNo', how='left') \
                            .merge(proposal_agg, on='UserNo', how='left') \
                            .merge(proj_agg, on='UserNo', how='left') \
                            .merge(perf_agg, on='UserNo', how='left') \
                            .merge(ops_agg, on='UserNo', how='left') \
                            .merge(supp_agg, on='UserNo', how='left') \
                            .fillna(0)

# 컬럼명 표시용으로 rename (내부 집계명 → 화면 표시명)
df_user_activity = df_user_activity.rename(columns={
    '총로그인수':   '총 로그인수',
    '제안서다운로드': '제안서 DL',
    '프로젝트찾기':  '프로젝트',
    '프로젝트실적':  '프로젝트 실적',
    '운영자료 찾기': '운영자료',
    '서포트센터':   '서포트 센터',
})

# 숫자형 변환
count_cols = ['총 로그인수', '제안서 DL', '프로젝트', '프로젝트 실적', '운영자료', '서포트 센터']
for c in count_cols:
    df_user_activity[c] = df_user_activity[c].astype(int)

with col_s1_left:
    st.markdown('<div class="headline" style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">👤 직원별 활동 상세내역</div>', unsafe_allow_html=True)
    # 조건부 서식 적용 (제안서 DL 컬럼에만 빨간색 표시)
    def highlight_proposal(val):
        color = '#ef4444' if isinstance(val, (int, float)) and val >= warning_threshold else ''
        background = '#fee2e2' if color else ''
        return f'color: {color}; background-color: {background}; font-weight: bold;' if color else ''

    _activity_sorted = df_user_activity.sort_values(['제안서 DL', '총 로그인수'], ascending=False).reset_index(drop=True)
    _activity_sorted.index += 1
    _activity_sorted.index.name = 'NO.'
    _act_num = _activity_sorted.select_dtypes(include='number').columns.tolist()
    styled_activity = _activity_sorted.style.map(
        highlight_proposal, subset=['제안서 DL']
    ).set_properties(subset=_act_num, **{'text-align': 'center'})
    st.dataframe(styled_activity, use_container_width=True, hide_index=False, height=300)

with col_s1_right:
    # 제안서 경고 횟수 설정 (UI 위치 복구)
    warning_threshold = st.selectbox(
        "제안서 경고 횟수 설정",
        options=[5, 10, 15, 20, 30, 50, 100],
        index=1,
        key='user_page_threshold_v2'
    )
    # 세션 상태 업데이트 (페이지 간 공유 및 유지 용도)
    st.session_state['warning_threshold'] = warning_threshold

    st.markdown('<div class="headline" style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">🚨 제안서 다운로드 현황</div>', unsafe_allow_html=True)

    heavy_users = df_user_activity[df_user_activity['제안서 DL'] >= warning_threshold].copy()
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
    st.markdown('<div class="headline" style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">🕒 다운로드 타임라인</div>', unsafe_allow_html=True)
with col_t_filter:
    # 시간 단위를 드롭다운(selectbox)으로 설정 (변경: 1시간 ~ 24시간)
    time_options = ["전체 로그"] + [f"{i}시간" for i in range(1, 25)]
    time_unit = st.selectbox("시간 단위", options=time_options, index=0, label_visibility="collapsed")

# 타임라인 데이터 준비 (제안서 기준)
tl_data = f_proposal.copy()

if selected_user != '전체 보기':
    tl_data = tl_data[tl_data['이름'] == selected_user]
else:
    # '전체 보기' 선택 시, 기준치(warning_threshold)를 초과한 모든 직원의 데이터만 필터링
    tl_data = tl_data[tl_data['UserNo'].isin(heavy_users['UserNo'])]

if not tl_data.empty:
    if time_unit != "전체 로그":
        h_val = int(time_unit.replace("시간", ""))
        window = timedelta(hours=h_val)

        results = []
        for user_no, group in tl_data.groupby('UserNo'):
            group = group.sort_values('date').reset_index(drop=True)
            i = 0
            while i < len(group):
                window_start = group.loc[i, 'date']
                window_end = window_start + window
                # 윈도우 범위 내 행 추출
                in_window = group[(group['date'] >= window_start) & (group['date'] < window_end)].copy()
                # 중복 문서 제외 (문서경로 기준)
                in_window_unique = in_window.drop_duplicates(subset=['문서경로'])
                unique_count = len(in_window_unique)

                for _, row in in_window_unique.iterrows():
                    results.append({
                        'UserNo': user_no,
                        '이름': row['이름'],
                        '부서': row['부서'],
                        '직급': row['직급'],
                        config.COL_NAME_EMAIL: row[config.COL_NAME_EMAIL],
                        '문서이름': row['문서경로'],
                        '열람시간': row['date'],
                        '윈도우시작': window_start,
                        '윈도우종료': window_end,
                        f'{h_val}시간내_순다운로드수': unique_count
                    })
                # 다음 윈도우는 현재 윈도우 마지막 행 다음부터
                i += len(in_window)

        if results:
            tl_display = pd.DataFrame(results)
            tl_display['열람시간'] = tl_display['열람시간'].dt.strftime('%Y-%m-%d %H:%M:%S')
            tl_display['윈도우시작'] = tl_display['윈도우시작'].dt.strftime('%Y-%m-%d %H:%M')
            tl_display['윈도우종료'] = tl_display['윈도우종료'].dt.strftime('%Y-%m-%d %H:%M')

            cols = ['UserNo', '이름', '부서', '직급', config.COL_NAME_EMAIL,
                    f'{h_val}시간내_순다운로드수', '윈도우시작', '문서이름', '열람시간']
            _tl_sorted = tl_display[cols].sort_values([f'{h_val}시간내_순다운로드수', '열람시간'], ascending=[False, False]).reset_index(drop=True)
            _tl_sorted.index += 1
            _tl_sorted.index.name = 'NO.'
            st.dataframe(
                _tl_sorted,
                use_container_width=True, hide_index=False, height=250
            )
        else:
            st.info("해당하는 다운로드 기록이 없습니다.")
    else:
        # 전체 로그: 중복 문서 제외 후 전체 표시
        tl_display = tl_data.drop_duplicates(subset=['UserNo', '문서경로'])[['UserNo', '이름', '부서', '직급', config.COL_NAME_EMAIL, '문서경로', 'date']].copy()
        tl_display.rename(columns={'문서경로': '문서이름', 'date': '열람시간'}, inplace=True)
        tl_display['열람시간'] = tl_display['열람시간'].dt.strftime('%Y-%m-%d %H:%M:%S')
        _tl_sorted = tl_display.sort_values('열람시간', ascending=False).reset_index(drop=True)
        _tl_sorted.index += 1
        _tl_sorted.index.name = 'NO.'
        st.dataframe(_tl_sorted, use_container_width=True, hide_index=False, height=250)
else:
    st.info("해당하는 다운로드 기록이 없습니다.")

st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# --- 6. 섹션 3: 다운로드 현황 (Top 7 / Top 10) ---
st.markdown('<div class="headline" style="font-size: 20px; font-weight: 800; color: #1e293b; margin-top: 32px; margin-bottom: 24px;">📊 카테고리별 다운로드 TOP 10</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
table_height = 280  # 높이 동일하게 조절

with c1:
    st.markdown("###### 📂 제안서 Top10")
    if not f_proposal.empty:
        def parse_project(path):
            match = re.search(r'/(\d{6})\[([^\]]+)\]', str(path))
            if match:
                return match.group(1), match.group(2)
            return None, None
        
        proj_info = f_proposal['문서경로'].apply(parse_project).apply(pd.Series)
        proj_info.columns = ['코드', '프로젝트명']
        top10_proj = proj_info.dropna().groupby(['코드', '프로젝트명']).size().reset_index(name='횟수')
        top10_proj = top10_proj.sort_values('횟수', ascending=False).head(10).reset_index(drop=True)
        top10_proj.index += 1
        top10_proj.index.name = 'NO.'
        st.dataframe(
            top10_proj.style.set_properties(subset=['횟수'], **{'text-align': 'center'}),
            use_container_width=True, hide_index=False, height=table_height,
        )
    else: st.info("데이터 없음")

with c2:
    st.markdown("###### 🔎 프로젝트 찾기 Top10")
    proj_logs = f_download[f_download['경로 메뉴명'].astype(str).str.contains('프로젝트 찾기', na=False)]
    if not proj_logs.empty:
        if '파일명' not in proj_logs.columns:
            proj_logs['파일명'] = proj_logs['경로 메뉴명'].apply(lambda x: str(x).split('/')[-1])
        
        top10_p = proj_logs.groupby('파일명').size().reset_index(name='횟수')
        top10_p.columns = ['파일명', '횟수']
        top10_p = top10_p.sort_values('횟수', ascending=False).head(10)[['파일명', '횟수']].reset_index(drop=True)
        top10_p.index += 1
        top10_p.index.name = 'NO.'
        st.dataframe(
            top10_p.style
                .set_properties(subset=['횟수'], **{'text-align': 'center', 'width': '52px', 'min-width': '52px'})
                .set_properties(subset=['파일명'], **{'max-width': '160px', 'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'}),
            use_container_width=True, hide_index=False, height=table_height,
        )
    else: st.info("데이터 없음")

with c3:
    st.markdown("###### 🛠️ 운영자료 찾기 Top10")
    ops_logs = f_download[f_download['경로 메뉴명'].astype(str).str.contains('운영자료 찾기', na=False)]
    if not ops_logs.empty:
        if '파일명' not in ops_logs.columns:
            ops_logs['파일명'] = ops_logs['경로 메뉴명'].apply(lambda x: str(x).split('/')[-1])
        
        top10_ops = ops_logs.groupby('파일명').size().reset_index(name='횟수')
        top10_ops.columns = ['파일명', '횟수']
        top10_ops = top10_ops.sort_values('횟수', ascending=False).head(10)[['파일명', '횟수']].reset_index(drop=True)
        top10_ops.index += 1
        top10_ops.index.name = 'NO.'
        st.dataframe(
            top10_ops.style
                .set_properties(subset=['횟수'], **{'text-align': 'center', 'width': '52px', 'min-width': '52px'})
                .set_properties(subset=['파일명'], **{'max-width': '160px', 'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'}),
            use_container_width=True, hide_index=False, height=table_height,
        )
    else: st.info("데이터 없음")

with c4:
    st.markdown("###### ☎️ 서포트 센터 Top10")
    supp_logs = f_download[f_download['경로 메뉴명'].astype(str).str.contains('서포트 센터', na=False)]
    if not supp_logs.empty:
        if '파일명' not in supp_logs.columns:
            supp_logs['파일명'] = supp_logs['경로 메뉴명'].apply(lambda x: str(x).split('/')[-1])
        
        top10_supp = supp_logs.groupby('파일명').size().reset_index(name='횟수')
        top10_supp.columns = ['파일명', '횟수']
        top10_supp = top10_supp.sort_values('횟수', ascending=False).head(10)[['파일명', '횟수']].reset_index(drop=True)
        top10_supp.index += 1
        top10_supp.index.name = 'NO.'
        st.dataframe(
            top10_supp.style
                .set_properties(subset=['횟수'], **{'text-align': 'center', 'width': '52px', 'min-width': '52px'})
                .set_properties(subset=['파일명'], **{'max-width': '160px', 'overflow': 'hidden', 'text-overflow': 'ellipsis', 'white-space': 'nowrap'}),
            use_container_width=True, hide_index=False, height=table_height,
        )
    else: st.info("데이터 없음")

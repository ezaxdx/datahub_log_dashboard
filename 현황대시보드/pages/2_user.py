import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import config

st.title("👤 2. User Monitor")
st.markdown(f"{config.CURRENT_YEAR}년 제안서 과다 다운로더 및 사용자별 활동 상세 분석을 수행합니다.")

# --- 1. 모니터링 설정 (이 페이지로 이동됨) ---
st.sidebar.markdown("---") # 사이드바에도 여전히 배치하여 접근성 유지 (원할 경우 본문 상단으로 이동 가능)
# 하지만 유저 요청에 따라 'User 페이지 안으로' 들어간다고 했으므로 본문 상단에 배치
with st.expander("🚨 모니터링 기준 설정", expanded=True):
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        warning_threshold = st.number_input(
            "제안서 과다 다운로드 기준치", 
            min_value=1, 
            value=st.session_state.get('warning_threshold', 10), 
            step=1,
            key='user_page_threshold'
        )
        st.session_state['warning_threshold'] = warning_threshold

# --- 2. 데이터 및 필터 적용 ---
df_proposal = st.session_state.get('df_proposal', pd.DataFrame())
sel_dept = st.session_state.get('sel_dept', [])
sel_rank = st.session_state.get('sel_rank', [])

def filter_user_data(df):
    if df.empty: return df
    res = df.copy()
    if sel_dept and '부서' in res.columns:
        res = res[res['부서'].isin(sel_dept)]
    if sel_rank and '직급그룹' in res.columns:
        res = res[res['직급그룹'].isin(sel_rank)]
    return res

f_proposal = filter_user_data(df_proposal)

# --- 3. 기준치 초과 사용자 분석 ---
if not f_proposal.empty:
    agg_cols = ['UserNo', '이름', '부서', '직급']
    if config.COL_NAME_EMAIL in f_proposal.columns:
        agg_cols.append(config.COL_NAME_EMAIL)
        
    user_counts = f_proposal.groupby(agg_cols).size().reset_index(name='다운로드수')
    heavy_users = user_counts[user_counts['다운로드수'] >= warning_threshold].sort_values(by='다운로드수', ascending=False)
    
    if not heavy_users.empty:
        st.warning(f"현재 필터 조건에서 총 {len(heavy_users)}명의 사용자가 기준치({warning_threshold}건)를 초과했습니다.")
        
        selected_user_name = st.selectbox("분석할 사용자 선택", options=heavy_users['이름'].tolist())
        selected_user_row = heavy_users[heavy_users['이름'] == selected_user_name].iloc[0]
        selected_user_no = selected_user_row['UserNo']
        
        user_logs = f_proposal[f_proposal['UserNo'] == selected_user_no].copy()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📍 고유 파일 열람 현황")
            doc_col = '문서경로' if '문서경로' in user_logs.columns else '비고' if '비고' in user_logs.columns else None
            if doc_col:
                unique_files = user_logs[doc_col].nunique()
                st.metric("고유 파일 열람 수", f"{unique_files}개")
            else:
                st.info("파일 상세 정보 없음")
            
        with col2:
            st.subheader("🕒 다운로드 타임라인")
            user_logs = user_logs.sort_values(by='date', ascending=False)
            disp_cols = ['date']
            if doc_col: disp_cols.append(doc_col)
            st.dataframe(user_logs[disp_cols], hide_index=True, use_container_width=True)
            
        st.markdown("---")
        st.subheader("📊 일자별 다운로드 추이")
        daily_user = user_logs.groupby(user_logs['date'].dt.date).size().reset_index(name='건수')
        daily_user.columns = ['날짜', '건수']
        fig = px.bar(daily_user, x='날짜', y='건수', title=f"{selected_user_name}님의 일자별 다운로드")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success(f"현재 필터 및 기준치({warning_threshold}건)를 초과한 사용자가 없습니다.")
else:
    st.info("조건에 맞는 데이터가 없습니다.")

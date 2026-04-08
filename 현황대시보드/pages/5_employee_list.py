import streamlit as st
import pandas as pd
import config

st.title("👥 6. Employee List")
st.markdown(f"{config.CURRENT_YEAR}년 기준 EZ데이터허브의 등록된 재직자 목록입니다.")

# --- 1. 데이터 가져오기 ---
df_u = st.session_state.get('df_users', pd.DataFrame())

# --- 2. 사이드바 필터 적용 ---
sel_dept = st.session_state.get('sel_dept', [])
sel_rank = st.session_state.get('sel_rank', [])

def filter_employee_list(df):
    if df.empty: return df
    res = df.copy()
    
    # 부서 필터
    if sel_dept and '_ui_dept' in res.columns:
        res = res[res['_ui_dept'].isin(sel_dept)]
    
    # 직급 그룹 필터
    if sel_rank:
        rank_col = config.YEAR_COL_RANK.format(year=config.CURRENT_YEAR)
        def group_rank_master(row):
            rank = row.get(rank_col)
            if pd.isna(rank): return '기타'
            r_str = str(rank).strip()
            if r_str in ['사원', '대리', '주임', '연구원']: return '실무자(사원/대리)'
            if r_str in ['차장', '팀장', '부장', '본부장', '이사', '실장', '수석', '상무', '전무']: return '관리자(차장↑)'
            return '기타'
        res['_ui_rank_group'] = res.apply(group_rank_master, axis=1)
        res = res[res['_ui_rank_group'].isin(sel_rank)]
        
    return res

f_user_list = filter_employee_list(df_u)

# --- 3. 데이터 표시 ---
if not f_user_list.empty:
    st.info(f"현재 필터링된 재직자: {len(f_user_list):,}명")
    
    # 표시용 컬럼 정제
    rank_col = config.YEAR_COL_RANK.format(year=config.CURRENT_YEAR)
    email_col = config.COL_NAME_EMAIL
    
    target_cols = ['UserNo', '임직원명', '_ui_dept', rank_col, email_col, '입사일자']
    available_cols = [c for c in target_cols if c in f_user_list.columns]
    
    display_list = f_user_list[available_cols].copy()
    
    # 컬럼명 매핑 (UserNo, 이름, 부서, 직위/직급, PRS ID, 입사일자)
    rename_map = {
        '임직원명': '이름', 
        '_ui_dept': '부서', 
        rank_col: '직급'
    }
    display_list = display_list.rename(columns=rename_map)
    
    # 테이블 출력
    st.dataframe(
        display_list, 
        hide_index=True, 
        use_container_width=True,
        height=600
    )
    
    # CSV 다운로드 버튼
    csv = display_list.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 직원 리스트 다운로드 (CSV)",
        data=csv,
        file_name=f"EZ데이터허브_직원리스트_{config.CURRENT_YEAR}.csv",
        mime="text/csv",
    )
else:
    st.warning("조건에 맞는 직원이 없습니다. 필터를 확인해 주세요.")

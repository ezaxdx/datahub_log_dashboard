import streamlit as st
import pandas as pd
import config

# --- [Page Header] ---
st.markdown(f"""
<div class="page-header">
    <div style="font-size: 10px; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-family: 'Inter';">Human Resources</div>
    <div style="font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 4px; font-family: 'Manrope';">{config.CURRENT_YEAR} EZ데이터허브 임직원 명부</div>
    <div style="font-size: 14px; color: #64748b; font-weight: 400; font-family: 'Inter';">데이터허브에 등록된 재직자 목록 및 부서 정보를 확인합니다.</div>
</div>
""", unsafe_allow_html=True)

# --- 1. 데이터 가져오기 ---
df_u = st.session_state.get('df_users', pd.DataFrame())

# --- 2. 전체 직원 표시 (사이드바 필터 무관) ---
f_user_list = df_u.copy()

# --- 3. 데이터 표시 ---
if not f_user_list.empty:
    st.markdown(f'<div class="headline" style="font-size: 20px; font-weight: 800; color: #1e293b; margin-bottom: 16px;">👥 전체 임직원 목록 <span style="font-size: 14px; font-weight: 400; color: #64748b; margin-left: 8px;">(총 {len(f_user_list):,}명)</span></div>', unsafe_allow_html=True)
    
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

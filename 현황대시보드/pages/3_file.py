import streamlit as st
import config

st.title("📁 3. File Analysis")
st.markdown(f"{config.CURRENT_YEAR}년 EZ데이터허브 시스템 내 파일 업로드 및 다운로드 현황을 분석합니다.")

st.info("🚧 해당 페이지는 서비스 준비 중입니다. (Stage 2 구현 대상)")
st.divider()

col1, col2 = st.columns(2)
with col1:
    st.subheader("인기 파일 TOP 10")
    st.write("다운로드 수가 많은 파일을 순위별로 표시할 예정입니다.")

with col2:
    st.subheader("파일 타입 분포")
    st.write("PDF, PPTX, DOCX 등 파일 형식별 통계를 제공할 예정입니다.")

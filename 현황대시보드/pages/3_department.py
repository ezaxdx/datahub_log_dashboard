import streamlit as st
import config

st.title("🏢 4. Dept & Team")
st.markdown(f"{config.CURRENT_YEAR}년 부서별 활용도 분석 및 {config.PREV_YEAR}년 대비 성장률을 제공합니다.")

st.info("🚧 해당 페이지는 서비스 준비 중입니다. (Stage 2 구현 대상)")
st.divider()

st.subheader("부서별 성과 지표")
st.write("부서 내 접속자 수, 평균 다운로드 수 등을 종합하여 성과를 점수화할 예정입니다.")

st.subheader("연도별 비교 트렌드")
st.write(f"{config.PREV_YEAR}년과 {config.CURRENT_YEAR}년의 부서별 데이터 비교를 차트로 제공할 예정입니다.")

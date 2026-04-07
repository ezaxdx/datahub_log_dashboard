import streamlit as st

st.set_page_config(
    page_title="Antigravity News",
    page_icon="🚀",
    layout="wide"
)

def main():
    # 사이드바 구성
    st.sidebar.title("🚀 Antigravity News")
    st.sidebar.markdown("나만의 AI IT 뉴스룸")
    
    # 네비게이션
    page = st.sidebar.radio("Navigation", ["뉴스룸 브리핑", "관리자 대시보드"])
    
    if page == "뉴스룸 브리핑":
        show_newsroom()
    elif page == "관리자 대시보드":
        show_admin_dashboard()

def show_newsroom():
    st.title("📰 2023년 10월 27일 IT 리포트")
    st.markdown("### 🚀 오늘의 AI 동향")
    
    with st.expander("오늘의 주요 뉴스 요약", expanded=True):
        st.markdown("""
        **1. 핵심 내용**
        - 구글, 새로운 AI 모델 발표 예정...
        - 오픈AI, 챗GPT 업데이트...
        
        **2. 시사점**
        - AI 기술의 발전 속도가 점차 빨라지고 있어 지속적인 모니터링이 필요함.
        """)
        
    st.metric(label="오늘의 방문자 수", value="25", delta="13")

def show_admin_dashboard():
    st.title("⚙️ 관리자 대시보드")
    
    # 향후 비밀번호 인증 로직 추가 예정
    tab1, tab2, tab3 = st.tabs(["피드 편집", "분석 실행", "데이터 통계"])
    
    with tab1:
        st.subheader("RSS 피드 관리")
        st.write("현재 등록된 피드 목록...")
        st.text_input("새로운 RSS URL 입력")
        st.button("추가")
        
    with tab2:
        st.subheader("수집 및 분석 메뉴(수동 실행)")
        if st.button("🚀 스크래핑 및 AI 분석 시작"):
            st.info("수집을 시작합니다...")
            
    with tab3:
        st.subheader("방문자 수 추이")
        st.line_chart({"2023-10-26": [12], "2023-10-27": [25]})

if __name__ == "__main__":
    main()

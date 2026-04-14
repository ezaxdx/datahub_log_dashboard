# Antigravity Dashboard Revision History

이 문서는 Antigravity 현황 대시보드의 주요 발전 단계와 버전별 변경 사항을 기록합니다.

---

## [Phase 3] v1.4.0. Multi-Page Module & UX Tuning (2026-04-10)
**"전문 분석 도구로의 확장 및 사용자 경험 최적화"**

### [v1.4.x] UI/UX Optimization
- **Single-Screen Layout**: 브라우저 100% 확대 시 스크롤 없이 주요 지표 노출 (차트 높이 및 여백 최적화).
- **Navigation Improvement**: '분석 대상 로그' 선택박스를 섹션 헤더 우측으로 배치하여 접근성 향상.
- **Naming Standard**: 전역 명칭 '소속불분명'을 전문 명칭인 **'M-Level'**로 일괄 변경.

### [v1.3.x] Specialized Analytics (3_department.py)
- **Custom Grouping**: 본부/실 기준의 부서 그룹핑(`부서_그룹`) 로직 구현.
- **Advanced Filtering**: 활동 분석에서 특정 임원 위주 그룹(`M-Level`, `스마트관광 DC`) 제외 처리.
- **Personnel Table**: 팀별 합계 컬럼 추가 및 인원순 내림차순 정렬 적용.
- **Visual Polish**: -45도 차트 라벨 회전 처리로 겹침 현상 해결.

---

## [Phase 2] v1.0.0. Architecture Refactoring (2026-04-09)
**"디자인 프리미엄화 및 데이터 무결성 확보"**

### Core Logic Refactoring
- **Systematic Data Flow**: `data.py`를 통한 데이터 가공 중앙화 (Single Source of Truth).
- **Data Integrity**: `UserNo` 정규화 및 정보 미등록 사용자 필터링 로직 강화.
- **Configuration**: 전역 설정값(`config.py`) 및 공통 필터(사이드바) 시스템 구축.

### Premium UI/UX Design
- **Visual Identity**: 모던한 SaaS 스타일의 다크 블루/그레이 테마 적용.
- **Interactive Metrics**: 세련된 메트릭 카드 및 인터랙티브 필링 효과 도입.
- **Sync System**: 실시간 데이터 동기화(`st.session_state`) 버튼 구현.

---

## [Phase 1] v0.1.0. Initial Implementation (2026-03-xx)
**"데이터 시각화 프로토타입 개발"**

- Streamlit 환경 구축 및 원천 데이터 로드 엔진 개발.
- 로그인, 다운로드, 제안서 활동량에 대한 기초 대시보드 구현.
- 기간별(오늘, 최근 1주일 등) 활동 추이 차트 기본 프레임워크 구축.

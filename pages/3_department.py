import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import config

# --- 1. 페이지 헤더 ---
st.markdown(f"""
<div class="page-header">
    <div style="font-size: 10px; font-weight: 700; color: #10b981; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; font-family: 'Inter';">Organizational Insights</div>
    <div style="font-size: 28px; font-weight: 800; color: #1e293b; margin-bottom: 4px; font-family: 'Manrope';">{config.CURRENT_YEAR} 부서 및 직급별 활용 현황</div>
    <div style="font-size: 14px; color: #64748b; font-weight: 400; font-family: 'Inter';">부서와 직급별 인원 대비 활용도를 심층 분석합니다.</div>
</div>
""", unsafe_allow_html=True)

# --- 2. 데이터 가져오기 ---
df_u = st.session_state.get('df_users', pd.DataFrame())
df_login = st.session_state.get('df_login', pd.DataFrame())
df_download = st.session_state.get('df_download', pd.DataFrame())
df_proposal = st.session_state.get('df_proposal', pd.DataFrame())

date_preset = st.session_state.get('date_preset', '전체')
date_range = st.session_state.get('date_range', None)
sel_dept = st.session_state.get('sel_dept', [])
sel_rank = st.session_state.get('sel_rank', [])

# 데이터 무결성 체크 (새로운 컬럼 '부서_그룹' 유무 확인)
if not df_u.empty and '부서_그룹' not in df_u.columns:
    st.error("⚠️ 데이터 구조가 업데이트되었습니다. 사이드바 상단의 [🔄 최신 데이터 동기화] 버튼을 클릭하여 데이터를 갱신해 주세요.")
    st.stop()

# --- 3. 데이터 필터링 ---
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
    
    # 사이드바 공통 필터 적용 (부서/직급그룹)
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

# (로그 분기 처리는 아래 섹션 집계 전에 수행됨)

# (데이터 필터링 완료 후, 하단 UI 섹션에서 로그 종류에 따른 active_df 분기 처리를 수행합니다.)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)



# --- 5. 섹션 1: 부서별 사용 현황 ---
# 한 줄 배치: 제목은 왼쪽, 로그 선택은 오른쪽
col_dept_title, col_log_sel = st.columns([3, 1])

with col_dept_title:
    st.markdown('<div class="headline" style="font-size: 20px; font-weight: 800; color: #1e293b;">🏢 부서별 사용 현황</div>', unsafe_allow_html=True)

with col_log_sel:
    target_log_type = st.selectbox(
        "로그 선택",
        ["로그인", "제안서", "다운로드 전체", "프로젝트 찾기", "운영자료 찾기", "서포트센터"],
        index=0,
        label_visibility="collapsed"
    )

# --- 4. 분석 대상 로그에 따른 데이터 분기 (정의 직후 수행) ---

# --- 4. 분석 대상 로그에 따른 데이터 분기 (정의 직후 수행) ---
if target_log_type == "로그인":
    active_df = f_login
elif target_log_type == "제안서":
    active_df = f_proposal
elif target_log_type == "다운로드 전체":
    active_df = pd.concat([f_download, f_proposal])
elif target_log_type == "프로젝트 찾기":
    active_df = f_download[f_download['경로 메뉴명'].astype(str).str.contains("프로젝트", na=False)]
elif target_log_type == "운영자료 찾기":
    active_df = f_download[f_download['경로 메뉴명'].astype(str).str.contains("운영자료", na=False)]
elif target_log_type == "서포트센터":
    active_df = f_download[f_download['경로 메뉴명'].astype(str).str.contains("서포트", na=False)]
else:
    active_df = f_login

# 데이터 유무 확인 및 특정 그룹 제외 정규화
if active_df.empty:
    st.info(f"선택한 조건의 '{target_log_type}' 데이터가 없습니다.")
    st.stop()

# [최종] 제외 그룹 명칭 확정 (사용자 요청 반영: 딱 2개 그룹만 제외)
exclude_groups = ["M-Level", "스마트관광 디지털융합혁신"]
_null_strs = {'None', 'nan', ''}
active_df = active_df[
    ~active_df['부서_그룹'].isin(exclude_groups) &
    active_df['부서_그룹'].notna() &
    ~active_df['부서_그룹'].astype(str).str.strip().isin(_null_strs)
]

# 집계 (부서_그룹 기준)
dept_counts = active_df.groupby('부서_그룹').size().reset_index(name='횟수')
dept_unique = active_df.groupby('부서_그룹')['UserNo'].nunique().reset_index(name='순사용자')
# 인원수 매핑 (df_users 기준 - 전체 부서 목록 확보)
dept_members = f_u.groupby('부서_그룹').size().reset_index(name='전체인원')

# 모든 부서가 나오도록 부서 인원수 데이터를 기준으로 조인
dept_data = pd.merge(dept_members, dept_counts, on='부서_그룹', how='left')
dept_data = pd.merge(dept_data, dept_unique, on='부서_그룹', how='left').fillna(0)

dept_data['인원대비활동'] = (dept_data['횟수'] / dept_data['전체인원']).replace([float('inf'), -float('inf')], 0).fillna(0).round(2)
dept_data['사용률'] = (dept_data['순사용자'] / dept_data['전체인원'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0).round(1)

# [추가] 활동량 차트에서도 제외 그룹 반영 (0건인 부서 노출 방지)
dept_data = dept_data[~dept_data['부서_그룹'].isin(exclude_groups)]
dept_data = dept_data.sort_values(by='횟수', ascending=True)

# 차트 (세로 막대)
fig_dept = px.bar(
    dept_data, 
    x='부서_그룹', 
    y='횟수', 
    color='횟수',
    color_continuous_scale=['#f1f5f9', '#0f172a'],
    text='사용률',
    custom_data=['전체인원', '인원대비활동', '순사용자', '사용률']
)
fig_dept.update_traces(
    hovertemplate="<b>%{x}</b><br>활동량: %{y}건<br>소속인원: %{customdata[0]}명<br>순사용자: %{customdata[2]}명<br><b>사용률: %{customdata[3]}%</b><br>인당 활동량: %{customdata[1]}건",
    texttemplate="%{text}%", textposition="outside", cliponaxis=False
)

# 회사 평균선 (부서당 평균 활동량)
avg_val = dept_data['횟수'].mean()
fig_dept.add_hline(y=avg_val, line_dash="dash", line_color="#ef4444", 
                  annotation_text=f"전사 평균: {avg_val:.1f}건", annotation_position="top right")

# X축 라벨 회전 설정
fig_dept.update_xaxes(tickangle=-45, tickfont=dict(size=10))

fig_dept.update_layout(
    height=310,
    margin=dict(l=10, r=10, t=30, b=80),
    xaxis_title=None, yaxis_title=None,
    showlegend=False,
    coloraxis_showscale=False,
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#64748b", family='Inter')),
    yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickfont=dict(size=10, color="#64748b", family='Inter'))
)
st.plotly_chart(fig_dept, use_container_width=True)

st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #eee;'>", unsafe_allow_html=True)


# 직급 정렬 기준 필터링 (데이터 가공 로직 복구)
rank_order_no_exec = [r for r in config.RANK_ORDER if r != '임원']
rank_data = active_df[active_df['직급'].isin(rank_order_no_exec)]

if not rank_data.empty:
    rank_counts = rank_data.groupby('직급').size().reset_index(name='횟수')
    rank_unique = rank_data.groupby('직급')['UserNo'].nunique().reset_index(name='순사용자')
    # 인원수 매핑 (임원 제외 전체 직급 목록 확보)
    all_ranks_no_exec = f_u[f_u['직급'].isin(rank_order_no_exec)]
    rank_members = all_ranks_no_exec.groupby('직급').size().reset_index(name='전체인원')
    
    # 모든 직급이 나오도록 직급 인원수 데이터를 기준으로 조인
    rank_chart_data = pd.merge(rank_members, rank_counts, on='직급', how='left')
    rank_chart_data = pd.merge(rank_chart_data, rank_unique, on='직급', how='left').fillna(0)
    rank_chart_data['사용률'] = (rank_chart_data['순사용자'] / rank_chart_data['전체인원'] * 100).replace([float('inf'), -float('inf')], 0).fillna(0).round(1)
    
    # 정렬 (config.RANK_ORDER 역순)
    rank_chart_data['rank_idx'] = rank_chart_data['직급'].apply(lambda x: config.RANK_ORDER.index(x) if x in config.RANK_ORDER else 99)
    rank_chart_data = rank_chart_data.sort_values(by='rank_idx', ascending=False)

# 컬럼 분할 (직급별 현황 vs 실무자/관리자 비중)
col_rank_main, col_rank_sub = st.columns([2, 1])

with col_rank_main:
    st.markdown('<div class="headline" style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">🎓 직급별 사용 현황 (임원 제외)</div>', unsafe_allow_html=True)
    if not rank_data.empty:
        fig_rank = px.bar(
            rank_chart_data,
            x='직급',
            y='횟수',
            color='횟수',
            color_continuous_scale=['#f1f5f9', '#0f172a'],
            text='사용률',
            custom_data=['전체인원', '사용률']
        )
        
        fig_rank.update_traces(
            hovertemplate="<b>%{x}</b><br>활동량: %{y}건<br>소속인원: %{customdata[0]}명<br><b>사용률: %{customdata[1]}%</b>",
            texttemplate="%{text}%", textposition="outside", cliponaxis=False
        )
        
        # 회사 평균선 (직급당 평균)
        avg_rank = rank_chart_data['횟수'].mean()
        fig_rank.add_hline(y=avg_rank, line_dash="dash", line_color="#ef4444", 
                          annotation_text=f"직급 평균: {avg_rank:.1f}건", annotation_position="top right")

        # 정렬 순서 강제 적용 (config.RANK_ORDER 기준)
        rank_order_xaxis = [r for r in config.RANK_ORDER if r in rank_chart_data['직급'].values]
        fig_rank.update_xaxes(categoryorder='array', categoryarray=rank_order_xaxis)

        fig_rank.update_layout(
            height=250, margin=dict(l=10, r=10, t=20, b=40),
            xaxis_title=None, yaxis_title=None,
            showlegend=False,
            coloraxis_showscale=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#64748b", family='Inter')),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9', tickfont=dict(size=10, color="#64748b", family='Inter'))
        )
        st.plotly_chart(fig_rank, use_container_width=True)
    else:
        st.info("임원을 제외한 직급의 활동 데이터가 없습니다.")

with col_rank_sub:
    st.markdown('<div class="headline" style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 16px;">📊 실무자/관리자 비중</div>', unsafe_allow_html=True)
    # 임원 제외 활동량 합계
    summary_data = active_df[active_df['직급그룹'].isin(['실무자(사원/대리)', '관리자(차장↑)'])]
    if not summary_data.empty:
        summary = summary_data.groupby('직급그룹').size().reset_index(name='횟수')
        fig_pie = px.pie(
            summary, 
            values='횟수', 
            names='직급그룹', 
            hole=0.5,
            color='직급그룹',
            color_discrete_map={'실무자(사원/대리)': '#10b981', '관리자(차장↑)': '#3b82f6'}
        )
        fig_pie.update_traces(textinfo='percent+label', textposition='outside', textfont=dict(size=11))
        fig_pie.update_layout(
            height=250, margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("비교 데이터 없음")

st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

# --- 7. 섹션 3: 인원표 ---
st.markdown('<div class="headline" style="font-size: 20px; font-weight: 800; color: #1e293b; margin-top: 32px; margin-bottom: 24px;">👥 부서/직급별 인원 현황</div>', unsafe_allow_html=True)

# 1. 전체 인원 피벗 (f_u 기준 - 제외 그룹 + None 필터링)
f_u_filtered = f_u[
    ~f_u['부서_그룹'].isin(exclude_groups) &
    f_u['부서_그룹'].notna() &
    ~f_u['부서_그룹'].astype(str).str.strip().isin(_null_strs) &
    f_u['직급'].notna() &
    ~f_u['직급'].astype(str).str.strip().isin(_null_strs)
]
total_pivot = pd.crosstab(f_u_filtered['부서_그룹'], f_u_filtered['직급'])

# 2. 순 사용자 피벗 (active_df 기준)
active_pivot = active_df.groupby(['부서_그룹', '직급'])['UserNo'].nunique().unstack(fill_value=0)

# 컬럼 순서 및 인덱스 정렬
cols = [r for r in config.RANK_ORDER if r in total_pivot.columns]
total_pivot = total_pivot[cols]
active_pivot = active_pivot.reindex(index=total_pivot.index, columns=total_pivot.columns, fill_value=0)

# "순사용자/총인원" 형식으로 결합
xtab = total_pivot.copy().astype(str)
for col in cols:
    # 각 셀을 "활동인원/전체인원"으로 표시
    xtab[col] = active_pivot[col].astype(int).astype(str) + "/" + total_pivot[col].astype(int).astype(str)

# 행별 합계: 피벗에 표시된 직급 컬럼 합산 → 크로스탭과 일관성 유지
# (f_u_filtered 전체를 쓰면 "정보미등록" 직급 포함되어 합계가 더 크게 나옴)
active_total_row = active_pivot.sum(axis=1).reindex(total_pivot.index, fill_value=0)
total_total_row  = total_pivot.sum(axis=1).reindex(total_pivot.index, fill_value=0)

xtab['합계'] = active_total_row.astype(int).astype(str) + "/" + total_total_row.astype(int).astype(str)

# 정렬 (총 인원 합계 기준 내림차순)
xtab = xtab.loc[total_total_row.sort_values(ascending=False).index]

st.dataframe(xtab, use_container_width=True)

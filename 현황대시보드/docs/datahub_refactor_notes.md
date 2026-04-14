# 사용률 계산식 검토 및 수정 사항

## 배경

Total 대시보드 및 부서/팀 대시보드의 사용률 계산식 정합성 검토 중 발견된 이슈 및 확정된 설계 내용을 정리합니다.

---

## 수정 사항 1: 사용률 분모를 f_u 기준으로 통일

### 문제

사용률 계산 시 분자(순사용자)는 필터가 적용된 데이터(`f_proposal`, `f_download`)를 사용하지만, 분모(전체인원)는 필터가 적용되지 않은 원본 데이터(`df_u`)를 사용하고 있었음.

사이드바에서 특정 부서 또는 직급 필터를 적용하면 분모는 전사 전체 인원으로 유지되어 사용률이 실제보다 낮게 계산되는 왜곡 발생.

### 수정 내용

`db_u` → `f_u` 로 교체 (총 4곳)

**pages/dept_team.py**

```python
# 수정 전
dept_members = df_u.groupby('부서_그룹').size().reset_index(name='전체인원')
all_ranks_no_exec = df_u[df_u['직급'].isin(rank_order_no_exec)]

# 수정 후
dept_members = f_u.groupby('부서_그룹').size().reset_index(name='전체인원')
all_ranks_no_exec = f_u[f_u['직급'].isin(rank_order_no_exec)]
```

**pages/total.py**

```python
# 수정 전
total_users_dept = df_u.groupby('부서')['UserNo'].nunique().reset_index(name='전체인원')
total_users_rank = df_u.groupby('직급그룹')['UserNo'].nunique().reset_index(name='전체인원')

# 수정 후
total_users_dept = f_u.groupby('부서')['UserNo'].nunique().reset_index(name='전체인원')
total_users_rank = f_u.groupby('직급그룹')['UserNo'].nunique().reset_index(name='전체인원')
```

### 영향 범위

- 필터 미적용(전체) 상태에서는 `df_u == f_u` 이므로 결과 동일, 영향 없음
- 부서 또는 직급 필터 적용 시 분모가 필터 범위 내 인원으로 정확하게 계산됨

---

## 확정된 설계: 사용률 분자 기준

### 배경

사용률 분자(순사용자) 산정 시 로그인 포함 여부 검토.

### 확정

**로그인 제외, `f_proposal + f_download` 순사용자 기준 유지**

### 근거

KPI 항목이 "자료 다운로드 1인당 평균 횟수" 기준이므로, 로그인만 하고 다운로드하지 않은 사용자는 KPI 기여자로 보지 않음. 현재 로직이 KPI 정의와 일치하므로 변경하지 않음.

```python
active_p = f_proposal[['UserNo', '부서', '직급그룹']]
active_d = f_download[f_download['경로 메뉴명'].astype(str).str.contains('프로젝트|운영자료|서포트', na=False)][['UserNo', '부서', '직급그룹']]
active_users_all = pd.concat([active_p, active_d]).drop_duplicates(subset=['UserNo'])
```

---

## 수정 사항 2: 도넛차트 → 표 교체

### 대상 파일

`pages/total.py` 하단 4개 도넛차트 섹션

### 변경 후 구조

1행 4열로 구성, 도넛차트 4개를 TOP5 표로 교체

```
[부서별 로그인 TOP5] [부서별 사용률 TOP5] [직급별 로그인 TOP5] [직급별 사용률 TOP5]
```

### 각 표 계산 로직

**부서별 로그인 TOP5**

```python
login_dept_top5 = (
    f_login.groupby('부서').size()
    .reset_index(name='로그인수')
    .sort_values('로그인수', ascending=False)
    .head(5)
    .reset_index(drop=True)
)
```

**부서별 사용률 TOP5**

```python
active_by_dept = active_users_all.groupby('부서')['UserNo'].nunique().reset_index(name='순사용자')
total_users_dept = f_u.groupby('부서')['UserNo'].nunique().reset_index(name='전체인원')
usage_dept = pd.merge(total_users_dept, active_by_dept, on='부서', how='left').fillna(0)
usage_dept['사용률(%)'] = (usage_dept['순사용자'] / usage_dept['전체인원'] * 100).round(1)
usage_dept_top5 = (
    usage_dept[['부서', '전체인원', '순사용자', '사용률(%)']]
    .sort_values('사용률(%)', ascending=False)
    .head(5)
    .reset_index(drop=True)
)
```

**직급별 로그인 TOP5**

```python
login_rank_top5 = (
    f_login.groupby('직급그룹').size()
    .reset_index(name='로그인수')
    .sort_values('로그인수', ascending=False)
    .head(5)
    .reset_index(drop=True)
)
```

**직급별 사용률 TOP5**

```python
active_by_rank = active_users_all.groupby('직급그룹')['UserNo'].nunique().reset_index(name='순사용자')
total_users_rank = f_u.groupby('직급그룹')['UserNo'].nunique().reset_index(name='전체인원')
usage_rank = pd.merge(total_users_rank, active_by_rank, on='직급그룹', how='left').fillna(0)
usage_rank['사용률(%)'] = (usage_rank['순사용자'] / usage_rank['전체인원'] * 100).round(1)
usage_rank_top5 = (
    usage_rank[['직급그룹', '전체인원', '순사용자', '사용률(%)']]
    .sort_values('사용률(%)', ascending=False)
    .head(5)
    .reset_index(drop=True)
)
```

### 레이아웃

```python
col_t1, col_t2, col_t3, col_t4 = st.columns(4)

with col_t1:
    st.markdown("##### 부서별 로그인 TOP5")
    st.dataframe(login_dept_top5, use_container_width=True, hide_index=True)

with col_t2:
    st.markdown("##### 부서별 사용률 TOP5")
    st.dataframe(usage_dept_top5, use_container_width=True, hide_index=True)

with col_t3:
    st.markdown("##### 직급별 로그인 TOP5")
    st.dataframe(login_rank_top5, use_container_width=True, hide_index=True)

with col_t4:
    st.markdown("##### 직급별 사용률 TOP5")
    st.dataframe(usage_rank_top5, use_container_width=True, hide_index=True)
```

### 삭제 대상

기존 도넛차트 관련 코드 전체 삭제

- `get_color_map()` 함수
- `dept_color_map`, `rank_color_map` 변수
- `px.pie` 차트 4개

---

## 커밋 내역

```
fix: 사용률 분모를 f_u 기준으로 통일 (부서/직급 필터 반영)
refactor: 하단 도넛차트 4개를 TOP5 표로 교체
```

대상 파일: `pages/dept_team.py`, `pages/total.py`

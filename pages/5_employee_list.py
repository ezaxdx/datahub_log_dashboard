import streamlit as st
import pandas as pd
import json
import os
import config

# --- 재직 상태 오버라이드 헬퍼 ---
_OVERRIDES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "status_overrides.json")
_PROFILE_OVERRIDES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profile_overrides.json")

def _load_overrides() -> dict:
    try:
        if os.path.exists(_OVERRIDES_PATH):
            with open(_OVERRIDES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_overrides(overrides: dict):
    with open(_OVERRIDES_PATH, 'w', encoding='utf-8') as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)

def _load_profile_overrides() -> dict:
    try:
        if os.path.exists(_PROFILE_OVERRIDES_PATH):
            with open(_PROFILE_OVERRIDES_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_profile_overrides(overrides: dict):
    with open(_PROFILE_OVERRIDES_PATH, 'w', encoding='utf-8') as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)

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

# --- 2. 재직 상태 필터 ---
col_filter, col_count = st.columns([2, 3])
with col_filter:
    status_filter = st.radio(
        "재직 상태",
        options=["재직자만", "전체 (퇴사자 포함)"],
        horizontal=True,
        key="employee_status_filter"
    )

# 필터 적용
if '재직상태' in df_u.columns and status_filter == "재직자만":
    f_user_list = df_u[df_u['재직상태'] == '재직'].copy()
else:
    f_user_list = df_u.copy()

# --- 3. 데이터 표시 ---
# sort_cols를 if 블록 밖에서 미리 초기화 (expander에서도 참조하므로 스코프 보장)
sort_cols = []
for col in [
    config.YEAR_COL_DEPT.format(year=config.CURRENT_YEAR),
    config.YEAR_COL_HQ.format(year=config.CURRENT_YEAR),
    config.YEAR_COL_DIVISION.format(year=config.CURRENT_YEAR),
]:
    if col in df_u.columns:
        sort_cols.append(col)

if not f_user_list.empty:
    cnt_active  = len(df_u[df_u['재직상태'] == '재직']) if '재직상태' in df_u.columns else len(df_u)
    cnt_retired = len(df_u[df_u['재직상태'] == '퇴사']) if '재직상태' in df_u.columns else 0
    cnt_test    = len(df_u[df_u['재직상태'] == 'Test']) if '재직상태' in df_u.columns else 0

    with col_count:
        st.markdown(
            f"<div style='padding-top:8px; font-size:13px; color:#64748b;'>"
            f"재직 <b style='color:#1e293b'>{cnt_active}</b>명 &nbsp;|&nbsp; "
            f"퇴사 <b style='color:#94a3b8'>{cnt_retired}</b>명 &nbsp;|&nbsp; "
            f"Test <b style='color:#f59e0b'>{cnt_test}</b>명 &nbsp;|&nbsp; "
            f"합계 <b style='color:#1e293b'>{cnt_active + cnt_retired + cnt_test}</b>명"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown(f'<div class="headline" style="font-size: 20px; font-weight: 800; color: #1e293b; margin-bottom: 16px;">👥 임직원 목록 <span style="font-size: 14px; font-weight: 400; color: #64748b; margin-left: 8px;">(표시 {len(f_user_list):,}명)</span></div>', unsafe_allow_html=True)

    # 기본 정렬: Test 최하단 → 재직 → 퇴사 → 부서명 → 본부/실 → 사업부 → 이름 순
    _test_unos = set(str(u).zfill(3) for u in config.TEST_ACCOUNT_USERNOS)
    f_user_list = f_user_list.copy()
    f_user_list['_is_test']   = f_user_list['UserNo'].isin(_test_unos).astype(int)  # 0=일반, 1=테스트
    f_user_list['_is_retired'] = (f_user_list.get('재직상태', '재직') != '재직').astype(int)  # 0=재직, 1=퇴사
    sort_keys = ['_is_test', '_is_retired'] + sort_cols + (['임직원명'] if '임직원명' in f_user_list.columns else [])
    f_user_list = f_user_list.sort_values(sort_keys, na_position='last').drop(columns=['_is_test', '_is_retired']).reset_index(drop=True)

    # 표시용 컬럼 정제
    email_col = config.COL_NAME_EMAIL
    target_cols = ['UserNo', '임직원명', '_ui_dept', '직급', email_col, '입사일자', '퇴사일자', '재직상태']
    available_cols = [c for c in target_cols if c in f_user_list.columns]

    display_list = f_user_list[available_cols].copy()
    rename_map = {'임직원명': '이름', '_ui_dept': '부서'}
    display_list = display_list.rename(columns=rename_map)

    # 퇴사자/Test 행 색상 처리
    def highlight_retired(row):
        if row.get('재직상태') == '퇴사':
            return ['color: #94a3b8'] * len(row)
        if row.get('재직상태') == 'Test':
            return ['color: #f59e0b; font-style: italic'] * len(row)
        return [''] * len(row)

    display_list = display_list.reset_index(drop=True)
    display_list.index += 1
    display_list.index.name = 'NO.'
    styled = display_list.style.apply(highlight_retired, axis=1)

    st.dataframe(styled, hide_index=False, use_container_width=True, height=600)

    # CSV 다운로드
    csv = display_list.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 직원 리스트 다운로드 (CSV)",
        data=csv,
        file_name=f"EZ데이터허브_직원리스트_{config.CURRENT_YEAR}.csv",
        mime="text/csv",
    )

else:
    st.warning("조건에 맞는 직원이 없습니다. 필터를 확인해 주세요.")

# ────────────────────────────────────────────
# 재직 상태 수동 편집 (API 데이터 부정확 시 보정용)
# ────────────────────────────────────────────
st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

with st.expander("✏️ 재직 상태 / 부서 수동 편집", expanded=False):
    st.caption(
        "재직상태·부서를 직접 수정하세요. **Test** 로 지정하면 모든 집계에서 즉시 제외됩니다. "
        "**저장** 후 데이터가 자동 재로드됩니다."
    )

    if df_u.empty:
        st.info("데이터가 없습니다.")
    else:
        # 편집용: 전체 직원(재직·퇴사 모두) — 필터 무관
        edit_src = df_u.copy()
        if sort_cols:
            edit_src = edit_src.sort_values(sort_cols, na_position='last').reset_index(drop=True)

        edit_target = ['UserNo', '임직원명', '_ui_dept', '직급', '재직상태']
        edit_avail  = [c for c in edit_target if c in edit_src.columns]
        edit_df = edit_src[edit_avail].copy().rename(columns={'임직원명': '이름', '_ui_dept': '부서'})
        edit_df = edit_df.reset_index(drop=True)

        # 편집 불가 컬럼 (재직상태·부서만 수정 가능)
        readonly = [c for c in edit_df.columns if c not in ('재직상태', '부서')]
        col_cfg  = {c: st.column_config.TextColumn(disabled=True) for c in readonly}
        col_cfg['재직상태'] = st.column_config.SelectboxColumn(
            label='재직상태',
            options=['재직', '퇴사', 'Test'],
            required=True,
        )
        col_cfg['부서'] = st.column_config.TextColumn(label='부서')

        edited = st.data_editor(
            edit_df,
            column_config=col_cfg,
            hide_index=True,
            use_container_width=True,
            height=420,
            key='status_editor',
        )

        if st.button("💾 저장", type="primary", key="save_status_btn"):
            status_changed = edited['재직상태'] != edit_df['재직상태']
            dept_changed   = edited['부서'] != edit_df['부서']
            changed_mask   = status_changed | dept_changed

            if not changed_mask.any():
                st.info("변경 사항이 없습니다.")
            else:
                # 재직상태 오버라이드 저장
                if status_changed.any():
                    overrides = _load_overrides()
                    for _, row in edited[status_changed].iterrows():
                        overrides[str(row['UserNo'])] = row['재직상태']
                    _save_overrides(overrides)

                # 부서 오버라이드 저장 (profile_overrides.json)
                if dept_changed.any():
                    profiles = _load_profile_overrides()
                    for _, row in edited[dept_changed].iterrows():
                        uno = str(row['UserNo'])
                        if uno not in profiles:
                            profiles[uno] = {}
                        profiles[uno]['_ui_dept'] = row['부서']
                        profiles[uno]['부서'] = row['부서']
                    _save_profile_overrides(profiles)

                # 세션 초기화 → run_all() 재실행 (Test 제외 즉시 반영)
                for k in ['df_users', 'df_login', 'df_download', 'df_proposal']:
                    st.session_state.pop(k, None)

                names = ', '.join(edited[changed_mask]['이름'].tolist())
                st.success(f"✅ {changed_mask.sum()}명 저장 완료: {names}")
                st.rerun()

import streamlit as st
import pandas as pd
import json
import os
import config

# --- 재직 상태 오버라이드 헬퍼 ---
_OVERRIDES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "status_overrides.json")

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

    with col_count:
        st.markdown(
            f"<div style='padding-top:8px; font-size:13px; color:#64748b;'>"
            f"재직 <b style='color:#1e293b'>{cnt_active}</b>명 &nbsp;|&nbsp; "
            f"퇴사 <b style='color:#94a3b8'>{cnt_retired}</b>명 &nbsp;|&nbsp; "
            f"합계 <b style='color:#1e293b'>{cnt_active + cnt_retired}</b>명"
            f"</div>",
            unsafe_allow_html=True
        )

    st.markdown(f'<div class="headline" style="font-size: 20px; font-weight: 800; color: #1e293b; margin-bottom: 16px;">👥 임직원 목록 <span style="font-size: 14px; font-weight: 400; color: #64748b; margin-left: 8px;">(표시 {len(f_user_list):,}명)</span></div>', unsafe_allow_html=True)

    # 기본 정렬: 팀(부서명) → 본부/실 → 사업부 (sort_cols는 위에서 이미 계산됨)
    if sort_cols:
        f_user_list = f_user_list.sort_values(sort_cols, na_position='last').reset_index(drop=True)

    # 표시용 컬럼 정제
    email_col = config.COL_NAME_EMAIL
    target_cols = ['UserNo', '임직원명', '_ui_dept', '직급', email_col, '입사일자', '퇴사일자', '재직상태']
    available_cols = [c for c in target_cols if c in f_user_list.columns]

    display_list = f_user_list[available_cols].copy()
    rename_map = {'임직원명': '이름', '_ui_dept': '부서'}
    display_list = display_list.rename(columns=rename_map)

    # 퇴사자 행 회색 처리
    def highlight_retired(row):
        if row.get('재직상태') == '퇴사':
            return ['color: #94a3b8'] * len(row)
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

with st.expander("✏️ 재직 상태 수동 편집", expanded=False):
    st.caption(
        "API에서 입사일자·퇴사일자가 부정확하게 들어올 경우 여기서 직접 수정하세요. "
        "**저장** 하면 대시보드 전체에 즉시 반영되며, 다음 데이터 동기화 후에도 유지됩니다."
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

        # 편집 불가 컬럼 (재직상태만 수정 가능)
        readonly = [c for c in edit_df.columns if c != '재직상태']
        col_cfg  = {c: st.column_config.TextColumn(disabled=True) for c in readonly}
        col_cfg['재직상태'] = st.column_config.SelectboxColumn(
            label='재직상태',
            options=['재직', '퇴사'],
            required=True,
        )

        edited = st.data_editor(
            edit_df,
            column_config=col_cfg,
            hide_index=True,
            use_container_width=True,
            height=420,
            key='status_editor',
        )

        if st.button("💾 저장", type="primary", key="save_status_btn"):
            changed_mask = edited['재직상태'] != edit_df['재직상태']
            if not changed_mask.any():
                st.info("변경 사항이 없습니다.")
            else:
                changed_rows = edited[changed_mask]

                # 오버라이드 파일 업데이트
                overrides = _load_overrides()
                for _, row in changed_rows.iterrows():
                    overrides[str(row['UserNo'])] = row['재직상태']
                _save_overrides(overrides)

                # 세션 상태 즉시 반영
                df_u_updated = st.session_state.get('df_users', pd.DataFrame()).copy()
                if not df_u_updated.empty:
                    for _, row in changed_rows.iterrows():
                        mask = df_u_updated['UserNo'] == str(row['UserNo'])
                        df_u_updated.loc[mask, '재직상태'] = row['재직상태']
                    st.session_state['df_users'] = df_u_updated

                names = ', '.join(changed_rows['이름'].tolist())
                st.success(f"✅ {changed_mask.sum()}명 저장 완료: {names}")
                st.rerun()

"""
데이터 소스 정합성 비교 스크립트
Google Sheets vs REST API 주요 수치 비교

실행: python scratch/compare_sources.py
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import config

# ── 헬퍼 ──────────────────────────────────────────────
def fmt(n): return f"{n:,}" if isinstance(n, int) else str(n)

def summarize(label, df_u, df_l, df_dl, df_p):
    """로드된 4개 DataFrame의 핵심 수치를 딕셔너리로 반환"""
    import data as _data
    df_u2, df_l2, df_dl2, df_p2 = _data.preprocess_all(df_u, df_l, df_dl, df_p)
    df_u3, df_l3, df_dl3, df_p3 = _data.map_all(df_u2, df_l2, df_dl2, df_p2)

    def date_range(df):
        if df.empty or 'date' not in df.columns: return ("없음", "없음")
        s = df['date'].dropna()
        if s.empty: return ("없음", "없음")
        return (str(s.min().date()), str(s.max().date()))

    def cat_count(df, keyword):
        if df.empty or '경로 메뉴명' not in df.columns: return 0
        return int(df['경로 메뉴명'].astype(str).str.contains(keyword, na=False).sum())

    l_range  = date_range(df_l3)
    dl_range = date_range(df_dl3)
    p_range  = date_range(df_p3)

    active = int((df_u3['재직상태'] == '재직').sum()) if '재직상태' in df_u3.columns else len(df_u3)
    retired = int((df_u3['재직상태'] == '퇴사').sum()) if '재직상태' in df_u3.columns else 0

    return {
        # 건수
        "직원_전체":         len(df_u3),
        "직원_재직":         active,
        "직원_퇴사":         retired,
        "로그인_건수":       len(df_l3),
        "로그인_유저수":     int(df_l3['UserNo'].nunique()) if not df_l3.empty else 0,
        "다운로드_건수":     len(df_dl3),
        "다운로드_유저수":   int(df_dl3['UserNo'].nunique()) if not df_dl3.empty else 0,
        "제안서_건수":       len(df_p3),
        "제안서_유저수":     int(df_p3['UserNo'].nunique()) if not df_p3.empty else 0,
        # 날짜 범위
        "로그인_최초":       l_range[0],
        "로그인_최신":       l_range[1],
        "다운로드_최초":     dl_range[0],
        "다운로드_최신":     dl_range[1],
        "제안서_최초":       p_range[0],
        "제안서_최신":       p_range[1],
        # 카테고리 분포
        "프로젝트 찾기":     cat_count(df_dl3, '프로젝트'),
        "운영자료 찾기":     cat_count(df_dl3, '운영자료'),
        "서포트 센터":       cat_count(df_dl3, '서포트'),
        "기타":              cat_count(df_dl3, '기타'),
    }

# ── 1. REST API 로드 ───────────────────────────────────
print("=" * 60)
print("1/2  REST API 로드 중...")
print("=" * 60)
import data
config.DATA_SOURCE_MODE = "REST_API"

api_load = getattr(data.load_from_api, "__wrapped__", data.load_from_api)
df_u_api, df_l_api, df_dl_api, df_p_api = api_load()
print(f"  users={len(df_u_api)}  login={len(df_l_api)}  download={len(df_dl_api)}  proposal={len(df_p_api)}")
api = summarize("API", df_u_api, df_l_api, df_dl_api, df_p_api)
print("  완료")

# ── 2. Google Sheets 로드 ─────────────────────────────
print()
print("=" * 60)
print("2/2  Google Sheets 로드 중...")
print("=" * 60)
config.DATA_SOURCE_MODE = "GSPREAD"

gs_load = getattr(data.load_all, "__wrapped__", data.load_all)
try:
    df_u_gs, df_l_gs, df_dl_gs, df_p_gs = gs_load()
    print(f"  users={len(df_u_gs)}  login={len(df_l_gs)}  download={len(df_dl_gs)}  proposal={len(df_p_gs)}")
    gs = summarize("GSheet", df_u_gs, df_l_gs, df_dl_gs, df_p_gs)
    print("  완료")
    gs_ok = True
except Exception as e:
    print(f"  Google Sheets 연결 실패: {e}")
    gs_ok = False

# ── 3. 비교 출력 ──────────────────────────────────────
print()
print("=" * 60)
print("[ 정합성 비교 결과 ]")
print("=" * 60)

sections = [
    ("건수", [
        "직원_전체", "직원_재직", "직원_퇴사",
        "로그인_건수", "로그인_유저수",
        "다운로드_건수", "다운로드_유저수",
        "제안서_건수", "제안서_유저수",
    ]),
    ("날짜 범위", [
        "로그인_최초", "로그인_최신",
        "다운로드_최초", "다운로드_최신",
        "제안서_최초", "제안서_최신",
    ]),
    ("다운로드 카테고리", [
        "프로젝트 찾기", "운영자료 찾기", "서포트 센터", "기타"
    ]),
]

for section_name, keys in sections:
    print(f"\n  [{section_name}]")
    print(f"  {'항목':<18} {'GSheets':>10} {'REST API':>10} {'일치':>6}")
    print(f"  {'-'*18} {'-'*10} {'-'*10} {'-'*6}")
    for key in keys:
        gs_val  = gs.get(key, "N/A") if gs_ok else "N/A"
        api_val = api.get(key, "N/A")
        match   = "✓" if str(gs_val) == str(api_val) else "✗ 차이"
        if not gs_ok: match = "-"
        print(f"  {key:<18} {fmt(gs_val):>10} {fmt(api_val):>10} {match:>6}")

# 불일치 항목 요약
if gs_ok:
    mismatches = [k for s, keys in sections for k in keys
                  if str(gs.get(k)) != str(api.get(k))]
    print()
    if mismatches:
        print(f"  ⚠️  불일치 항목 {len(mismatches)}개: {', '.join(mismatches)}")
    else:
        print("  ✅  모든 항목 일치!")

# 원복
config.DATA_SOURCE_MODE = "REST_API"

print()
print("=" * 60)
print("비교 완료")
print("=" * 60)

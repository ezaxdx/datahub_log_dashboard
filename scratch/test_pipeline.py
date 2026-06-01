"""
데이터 파이프라인 단계별 테스트
실행: python scratch/test_pipeline.py
"""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
# REST_API 모드 강제
config.DATA_SOURCE_MODE = "REST_API"

# Streamlit mock (캐시 데코레이터 우회)
import unittest.mock as mock
import streamlit as st_mock

print("=" * 55)
print("STEP 1. load_from_api()")
print("=" * 55)
import data

try:
    # cache_data 우회: __wrapped__ 속성 사용
    fn = getattr(data.load_from_api, "__wrapped__", data.load_from_api)
    df_u, df_l, df_dl, df_p = fn()
    print(f"  users    : {len(df_u)}행  cols={list(df_u.columns[:5])}")
    print(f"  login    : {len(df_l)}행  cols={list(df_l.columns)}")
    print(f"  download : {len(df_dl)}행  cols={list(df_dl.columns)}")
    print(f"  proposal : {len(df_p)}행  cols={list(df_p.columns)}")
except Exception as e:
    import traceback
    print("  ERROR:"); traceback.print_exc(); sys.exit(1)

print()
print("=" * 55)
print("STEP 2. preprocess_all()")
print("=" * 55)
try:
    df_u2, df_l2, df_dl2, df_p2 = data.preprocess_all(df_u, df_l, df_dl, df_p)
    for name, df in [("login", df_l2), ("download", df_dl2), ("proposal", df_p2)]:
        if not df.empty and "date" in df.columns:
            valid = df["date"].notna().sum()
            sample = df["date"].dropna().head(2).tolist()
            print(f"  {name}: date 유효={valid}/{len(df)}  sample={sample}")
        else:
            print(f"  {name}: date 컬럼 없음 또는 비어있음  cols={list(df.columns)}")
except Exception as e:
    import traceback
    print("  ERROR:"); traceback.print_exc(); sys.exit(1)

print()
print("=" * 55)
print("STEP 3. map_all()")
print("=" * 55)
try:
    df_u3, df_l3, df_dl3, df_p3 = data.map_all(df_u2, df_l2, df_dl2, df_p2)
    for name, df in [("users", df_u3), ("login", df_l3), ("download", df_dl3), ("proposal", df_p3)]:
        dept_sample = df["_ui_dept"].value_counts().head(3).to_dict() if "_ui_dept" in df.columns else "없음"
        rank_sample = df["직급"].value_counts().head(3).to_dict() if "직급" in df.columns else "없음"
        print(f"  {name}: 행={len(df)}  부서샘플={dept_sample}  직급샘플={rank_sample}")
except Exception as e:
    import traceback
    print("  ERROR:"); traceback.print_exc(); sys.exit(1)

print()
print("=" * 55)
print("ALL PASS")
print("=" * 55)

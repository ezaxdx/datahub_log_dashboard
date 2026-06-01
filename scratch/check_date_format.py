"""
날짜 컬럼 원본값 진단 스크립트
- 구글 시트에서 날짜가 어떤 문자열로 오는지 확인
- pd.to_datetime 파싱 성공률 확인
실행: python scratch/check_date_format.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data
import pandas as pd

print("=" * 60)
print("데이터 로드 중 (구글 시트 연결)...")
print("=" * 60)

df_users, df_login, df_download, df_proposal = data.load_all()

def check_date_col(df, name, date_cols):
    print(f"\n▶ [{name}]")
    if df.empty:
        print("  ⚠️  데이터 없음")
        return
    for col in date_cols:
        if col not in df.columns:
            print(f"  ✗ '{col}' 컬럼 없음")
            continue
        samples = df[col].dropna().head(5).tolist()
        parsed  = pd.to_datetime(df[col], errors='coerce')
        nat_cnt = parsed.isna().sum()
        total   = len(df)
        print(f"  컬럼: '{col}'")
        print(f"  원본 샘플 (5개): {samples}")
        print(f"  파싱 결과: {total - nat_cnt}/{total}건 성공  |  실패(NaT): {nat_cnt}건")
        if nat_cnt > 0:
            bad_samples = df.loc[parsed.isna(), col].dropna().head(3).tolist()
            print(f"  ❌ 파싱 실패 샘플: {bad_samples}")
        else:
            print(f"  ✅ 전체 파싱 성공")

check_date_col(df_login,    "login",    ["로그인 일자", "로그인 시간"])
check_date_col(df_download, "download", ["다운로드 일자", "다운로드 시간"])
check_date_col(df_proposal, "제안서",   ["등록일", "등록시간"])

print("\n" + "=" * 60)
print("진단 완료")
print("=" * 60)

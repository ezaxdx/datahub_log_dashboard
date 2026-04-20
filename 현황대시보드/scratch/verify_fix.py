import data
import pandas as pd

def final_check():
    try:
        # 데이터 전체 로드 및 조인 실행
        df_u, df_l, df_d, df_p = data.run_all()
        
        # 매핑 실패(이름/부서 누락) 데이터 확인
        failed = df_p[df_p['UserNo'].isna() | (df_p['UserNo'].astype(str).str.strip() == '')]
        
        print(f"======================================")
        print(f"  [최종 검증 리포트]")
        print(f"--------------------------------------")
        print(f"  제안서 총 건수: {len(df_p)}건")
        print(f"  매핑 실패 건수: {len(failed)}건")
        
        if len(failed) == 0:
            print(f"  => 결과: 매핑 100% 성공 (성공)")
        else:
            print(f"  => 결과: 여전히 {len(failed)}건 매핑 실패 (점검 필요)")
            print(failed[['PRS ID', '번호']].head())
        print(f"======================================")

    except Exception as e:
        print(f"검증 중 오류 발생: {e}")

if __name__ == "__main__":
    final_check()

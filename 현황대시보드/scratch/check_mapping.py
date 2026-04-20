import data
import pandas as pd
import config

def diagnostic():
    df_u, _, _, df_p = data.run_all()
    # UserNo가 비어있는 행 추출
    failed = df_p[df_p['UserNo'].isna() | (df_p['UserNo'].astype(str).str.strip() == '')]
    
    print(f"Total Proposals: {len(df_p)}")
    print(f"Mapping Failed: {len(failed)}")
    
    if not failed.empty:
        print("\nSample of PRS ID in Failed Mapping:")
        print(failed['PRS ID'].unique()[:10])
        
        # 직원정보 이메일 공백 체크
        emails = df_u[config.COL_NAME_EMAIL].dropna().astype(str).tolist()
        has_space = [e for e in emails if e != e.strip()]
        print(f"\nEmails with hidden spaces in Master: {len(has_space)}")
        if has_space:
            print("Sample problematic master emails:", [f'\"{e}\"' for e in has_space[:3]])

if __name__ == "__main__":
    diagnostic()

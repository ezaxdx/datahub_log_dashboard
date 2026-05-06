import sys
sys.path.append(r"c:\김연아\@ AXDX팀\06. AI 툴 제작\01_EZ_Datahub_dashboard")

try:
    import data
    df_users, df_login, df_download, df_proposal = data.run_all()
    
    with open(r"c:\김연아\@ AXDX팀\06. AI 툴 제작\01_EZ_Datahub_dashboard\scratch\date_info.txt", "w", encoding="utf-8") as f:
        f.write(f"Login dates: {df_login['date'].min()} to {df_login['date'].max()}\n")
        f.write(f"Download dates: {df_download['date'].min()} to {df_download['date'].max()}\n")
        f.write(f"Proposal dates: {df_proposal['date'].min()} to {df_proposal['date'].max()}\n")
except Exception as e:
    with open(r"c:\김연아\@ AXDX팀\06. AI 툴 제작\01_EZ_Datahub_dashboard\scratch\date_info.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}\n")

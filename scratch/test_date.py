import sys
import os

# Add the dashboard path to sys.path so we can import config and data
dashboard_path = r"c:\김연아\@ AXDX팀\06. AI 툴 제작\01_EZ_Datahub_dashboard"
sys.path.append(dashboard_path)

# Mock streamlit before importing data
import streamlit as st
class MockSecrets:
    pass
st.secrets = MockSecrets()

import data

df_users, df_login, df_download, df_proposal = data.run_all()

print("Login Dates:", df_login['date'].min(), "to", df_login['date'].max())
print("Download Dates:", df_download['date'].min(), "to", df_download['date'].max())
print("Proposal Dates:", df_proposal['date'].min(), "to", df_proposal['date'].max())

# Try filtering logic
from datetime import date
start_date = date(2026, 1, 1)
end_date = date(2026, 1, 31)

def filter_dates(df):
    if df.empty: return 0
    if 'date' in df.columns:
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        return mask.sum()
    return 0

print("Jan 2026 Login Count:", filter_dates(df_login))
print("Jan 2026 Download Count:", filter_dates(df_download))
print("Jan 2026 Proposal Count:", filter_dates(df_proposal))

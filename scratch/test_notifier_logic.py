import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime, timedelta
import data
import notifier
import config

def test_intervals():
    start_time, end_time = notifier.get_check_interval()
    print(f"Current Time: {datetime.now()}")
    print(f"Check Interval Start: {start_time}")
    print(f"Check Interval End: {end_time}")
    
    interval_hour = 10 if start_time.hour == 10 else 16
    interval_key = f"{start_time.strftime('%Y-%m-%d')}_{interval_hour}"
    print(f"Interval Key: {interval_key}")
    
    records = notifier.get_notified_records()
    print(f"Current Notified Records: {records.get(interval_key, {})}")

if __name__ == "__main__":
    print("--- Notifier Logic Test ---")
    test_intervals()
    print("\n--- Getting Data ---")
    df_users, df_login, df_download, df_proposal = data.run_all()
    
    print("\n--- Current Data Stats ---")
    print(f"Download Rows: {len(df_download)}")
    print(f"Proposal Rows: {len(df_proposal)}")
    
    print("\n--- Running Notifier Check (Dry Run Mode) ---")
    # We won't actually send email, we'll just see what data gets filtered
    
    start_time, end_time = notifier.get_check_interval()
    
    def filter_by_time(df):
        if df.empty or 'date' not in df.columns: return pd.DataFrame()
        return df[(df['date'] >= start_time) & (df['date'] <= end_time)]

    f_d = filter_by_time(df_download)
    print(f"\nFiltered Download Rows in current interval: {len(f_d)}")
    if not f_d.empty:
        print(f"Max date in f_d: {f_d['date'].max()}, Min date: {f_d['date'].min()}")
        
    f_p = filter_by_time(df_proposal)
    print(f"Filtered Proposal Rows in current interval: {len(f_p)}")


import data
import pandas as pd
from datetime import datetime

def check_proposal_times():
    _, _, _, df_p = data.run_all()
    today = datetime.now().date()
    today_p = df_p[df_p['date'].dt.date == today]
    
    print(f"--- Today's Proposal Logs ({today}) ---")
    if today_p.empty:
        print("No logs found for today.")
    else:
        # 시간대별 분포 확인
        print(today_p[['이름', 'PRS ID', 'date']].sort_values('date'))
        
        # 알림용 Interval 계산 (notifier.py 로직 참고)
        now_hour = datetime.now().hour
        print(f"\nCurrent Time Hour: {now_hour}")
        print("Expected Interval start according to notifier.py:")
        if 10 <= now_hour < 16: print("10:01 AM")
        elif now_hour >= 16: print("16:01 PM")
        else: print("16:01 PM (Yesterday)")

if __name__ == "__main__":
    check_proposal_times()

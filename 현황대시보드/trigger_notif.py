import data
import notifier
import config
from datetime import datetime

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 알림 체크 자동 실행 시작...")
    
    try:
        # 1. 최신 데이터 로드 (Google Sheets에서 읽기)
        # data.load_all.clear() # 캐시 초기화 (필요시)
        df_users, df_login, df_download, df_proposal = data.run_all()
        
        # 2. 위험 감지 및 이메일 발송 실행
        notifier.run_auto_check(df_proposal, df_download)
        
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 알림 체크 완료.")
    except Exception as e:
        print(f"알림 체크 중 오류 발생: {e}")

if __name__ == "__main__":
    main()

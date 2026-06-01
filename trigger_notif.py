import sys
import data
import notifier
import config
from datetime import datetime

# 인코딩 UTF-8 고정 (작업 스케줄러/배치 파일 환경에서 로그 깨짐 방지)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 알림 체크 자동 실행 시작...")

    try:
        df_users, df_login, df_download, df_proposal = data.run_all()
        notifier.run_auto_check(df_proposal, df_download)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 알림 체크 완료.")
    except Exception as e:
        print(f"알림 체크 중 오류 발생: {e}")

if __name__ == "__main__":
    main()

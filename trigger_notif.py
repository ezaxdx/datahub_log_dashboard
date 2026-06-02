import sys
import os
import data
import notifier
import config
from datetime import datetime

# 작업 스케줄러 환경에서 stdout/stderr 인코딩을 UTF-8로 강제 (cp949 오류 방지)
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# 로그 파일 직접 쓰기 (UTF-8 고정)
_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints", "notifier_log.txt")

def log(msg):
    """UTF-8로 로그 파일에 직접 기록"""
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)
        with open(_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def main():
    log("알림 체크 자동 실행 시작...")
    try:
        df_users, df_login, df_download, df_proposal = data.run_all()
        result = notifier.run_auto_check(df_proposal, df_download)
        if result:
            log(f"완료 — {result.get('message', '')}")
        else:
            log("완료.")
    except Exception as e:
        log(f"오류 발생: {e}")

if __name__ == "__main__":
    main()

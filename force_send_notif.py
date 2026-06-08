"""
force_send_notif.py
오늘 10:00 ~ 현재까지 전체 구간을 강제 분석하여 메일 발송 (1회용)
- 중복 차단 레코드는 오늘 10시 구간(2026-06-08_10)만 초기화 후 재검사
"""
import sys
import os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from datetime import datetime
import data
import notifier
import config

# ── 오늘 10:00 ~ 지금 전체 구간으로 고정 ──────────────────────────
_start = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
_end   = datetime.now()
notifier.get_check_interval = lambda: (_start, _end)

print(f"[강제발송] 분석 구간: {_start.strftime('%H:%M')} ~ {_end.strftime('%H:%M')}")

# ── 오늘 10시 구간 체크포인트 초기화 (중복 차단 해제) ────────────────
import json
RECORDS_FILE = "checkpoints/notified_records.json"
try:
    with open(RECORDS_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)
except Exception:
    records = {}

today_key = datetime.now().strftime("%Y-%m-%d") + "_day"
if today_key in records:
    del records[today_key]
    with open(RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    print(f"[강제발송] '{today_key}' 체크포인트 초기화 완료")
else:
    print(f"[강제발송] '{today_key}' 체크포인트 없음 (초기화 불필요)")

# ── 데이터 로드 및 알림 실행 ────────────────────────────────────────
print("[강제발송] 데이터 로딩 중...")
df_users, df_login, df_download, df_proposal = data.run_all()

print("[강제발송] 알림 분석 실행 중...")
result = notifier.run_auto_check(df_proposal, df_download)

print(f"\n[강제발송] 결과: {result.get('message', result)}")

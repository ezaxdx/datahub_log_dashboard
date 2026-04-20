import pandas as pd
import os
import json
from datetime import datetime, timedelta
import config
import email_utils

# 알림 기록 파일 경로
NOTIFIED_RECORDS_FILE = "notified_records.json"

def get_check_interval():
    """
    현재 시각을 기준으로 분석할 시작 시각을 계산합니다.
    - 10:00 ~ 15:59 사이 실행 시: 오늘 10:01부터 현재까지
    - 16:00 ~ 익일 09:59 사이 실행 시: 최근 오후 16:01부터 현재까지
    """
    now = datetime.now()
    curr_hour = now.hour
    
    if 10 <= curr_hour < 16:
        # 오전 10시 이후 ~ 오후 4시 이전
        start_time = now.replace(hour=10, minute=1, second=0, microsecond=0)
    elif curr_hour >= 16:
        # 오늘 오후 4시 이후
        start_time = now.replace(hour=16, minute=1, second=0, microsecond=0)
    else:
        # 오늘 오전 10시 이전 (어제 오후 4시부터 시작)
        start_time = (now - timedelta(days=1)).replace(hour=16, minute=1, second=0, microsecond=0)
        
    return start_time, now

def get_notified_records():
    """알림 기록을 로드합니다."""
    if os.path.exists(NOTIFIED_RECORDS_FILE):
        try:
            with open(NOTIFIED_RECORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_notified_record(user_no, count, interval_key):
    """알림 기록을 저장합니다. (구간 키와 함께)"""
    records = get_notified_records()
    
    if interval_key not in records:
        records[interval_key] = {}
    
    records[interval_key][user_no] = count
    
    # 최근 기록만 유지 (파일 크기 관리용)
    if len(records) > 20:
        sorted_keys = sorted(records.keys())
        for k in sorted_keys[:-20]:
            del records[k]
            
    with open(NOTIFIED_RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def run_auto_check(df_proposal, df_download):
    """
    지정된 시간 구간 내의 모든 다운로드 기록을 분석하여 위험 인원을 감지하고 이메일을 발송합니다.
    """
    if df_proposal.empty and df_download.empty:
        return

    # 1. 분석 구간 설정 (사용자 요청: 오전 10시 / 오후 4시 기준)
    start_time, end_time = get_check_interval()
    # 구간 구분을 위한 키 생성 (예: 2024-04-20_10, 2024-04-20_16)
    interval_hour = 10 if start_time.hour == 10 else 16
    interval_key = f"{start_time.strftime('%Y-%m-%d')}_{interval_hour}"
    
    print(f"[Notifier] 구간 분석 시작: {start_time} ~ {end_time} (Key: {interval_key})")

    # 2. 대상 데이터 필터링 (구간 내 데이터 추출)
    def filter_by_time(df):
        if df.empty or 'date' not in df.columns: return pd.DataFrame()
        # 시/분/초가 포함된 date 컬럼으로 필터링
        return df[(df['date'] >= start_time) & (df['date'] <= end_time)]

    f_p = filter_by_time(df_proposal)
    f_d = filter_by_time(df_download)
    
    # 알림 대상 카테고리 필터링 (download 시트용)
    if not f_d.empty:
        cat_pattern = "|".join(config.ALERT_CATEGORIES)
        f_d = f_d[f_d['경로 메뉴명'].astype(str).str.contains(cat_pattern, na=False)].copy()
        f_d = f_d[['UserNo', '이름', '부서', '직급', '경로 메뉴명', 'date']]
        f_d.rename(columns={'경로 메뉴명': '문서경로'}, inplace=True)
    
    if not f_p.empty:
        # UserNo, 이름, 부서, 직급은 data.py의 join_master_info에서 처리됨
        available_cols = [col for col in ['UserNo', '이름', '부서', '직급', '문서경로', 'date'] if col in f_p.columns]
        f_p = f_p[available_cols]

    # 3. 데이터 통합 및 유저별 집계
    all_activity = pd.concat([f_p, f_d])
    if all_activity.empty:
        print("[Notifier] 해당 구간에 분석할 로그가 없습니다.")
        return

    agg = all_activity.groupby(['UserNo', '이름', '부서', '직급']).size().reset_index(name='총다운로드')
    
    # 상세 카테고리 추출 로직 (가장 빈도가 높은 카테고리)
    def get_top_category(user_no):
        user_rows = all_activity[all_activity['UserNo'] == user_no]
        if user_rows.empty: return "다운로드"
        cat_counts = {}
        for path in user_rows['문서경로'].astype(str):
            matched = False
            for cat in config.ALERT_CATEGORIES:
                if cat in path:
                    cat_counts[cat] = cat_counts.get(cat, 0) + 1
                    matched = True
                    break
            if not matched:
                cat_counts['기타'] = cat_counts.get('기타', 0) + 1
        return max(cat_counts, key=cat_counts.get)

    agg['상세카테고리'] = agg['UserNo'].apply(get_top_category)
    
    # 4. 위험 인원 추출 (구간 내 10건 이상)
    heavy_users = agg[agg['총다운로드'] >= config.NOTIFICATION_THRESHOLD].sort_values('총다운로드', ascending=False)
    
    if heavy_users.empty:
        print(f"[Notifier] 기준치({config.NOTIFICATION_THRESHOLD}건) 초과 인원 없음")
        return

    # 5. 중복 방지 필터링 (해당 구간에서 이미 알림을 보낸 이력 확인)
    records = get_notified_records().get(interval_key, {})
    
    new_risks = []
    for _, user in heavy_users.iterrows():
        u_no = str(user['UserNo'])
        last_count = records.get(u_no, 0)
        
        # 해당 구간 내에서 건수가 더 늘어난 경우에만 발송
        if user['총다운로드'] > last_count:
            new_risks.append(user)
            save_notified_record(u_no, int(user['총다운로드']), interval_key)

    if not new_risks:
        print("[Notifier] 신규 알림 대상 없음 (동일 구간 기발송 건)")
        return

    # 6. 이메일 발송
    new_risks_df = pd.DataFrame(new_risks)
    rep_cat = new_risks_df['상세카테고리'].value_counts().idxmax()
    if len(new_risks_df['상세카테고리'].unique()) > 1: rep_cat += " 외"
        
    date_suffix = start_time.strftime('%Y%m%d')
    subject = f"[EZ데이터허브] {rep_cat} 다운로드 횟수 초과 안내_{date_suffix}"
    
    html = email_utils.build_risk_alert_html(new_risks_df, config.NOTIFICATION_THRESHOLD)
    email_utils.send_email(subject, html)

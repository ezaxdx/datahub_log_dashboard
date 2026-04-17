import pandas as pd
import os
import json
from datetime import datetime
import config
import email_utils

# 알림 기록 파일 경로
NOTIFIED_RECORDS_FILE = "notified_records.json"

def get_notified_records():
    """알림 기록을 로드합니다."""
    if os.path.exists(NOTIFIED_RECORDS_FILE):
        try:
            with open(NOTIFIED_RECORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_notified_record(user_no, count):
    """알림 기록을 저장합니다. (오늘 날짜와 함께)"""
    records = get_notified_records()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if today not in records:
        records[today] = {}
    
    records[today][user_no] = count
    
    with open(NOTIFIED_RECORDS_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def run_auto_check(df_proposal, df_download):
    """
    모든 다운로드 기록을 분석하여 위험 인원을 감지하고 이메일을 발송합니다.
    """
    if df_proposal.empty and df_download.empty:
        return

    # 1. 대상 데이터 통합 및 필터링
    # 제안서 데이터 가공
    p_data = df_proposal[['UserNo', '이름', '부서', '직급', '문서경로']].copy() if not df_proposal.empty else pd.DataFrame()
    
    # 일반 다운로드 중 알림 대상 카테고리만 필터링
    d_data = pd.DataFrame()
    if not df_download.empty:
        cat_pattern = "|".join(config.ALERT_CATEGORIES)
        d_data = df_download[df_download['경로 메뉴명'].astype(str).str.contains(cat_pattern, na=False)].copy()
        d_data = d_data[['UserNo', '이름', '부서', '직급', '경로 메뉴명']]
        d_data.rename(columns={'경로 메뉴명': '문서경로'}, inplace=True)
    
    # 통합
    all_activity = pd.concat([p_data, d_data])
    if all_activity.empty:
        return

    # 2. 유저별 집계
    agg = all_activity.groupby(['UserNo', '이름', '부서', '직급']).size().reset_index(name='총다운로드')
    
    # 상세 내용 (가장 많이 발생한 카테고리 추출)
    def get_top_category(user_no):
        user_rows = all_activity[all_activity['UserNo'] == user_no]
        if user_rows.empty: return "다운로드"
        
        # 문서경로에서 ALERT_CATEGORIES 기반으로 카테고리 판별
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
        
        # 가장 빈도가 높은 카테고리 반환
        return max(cat_counts, key=cat_counts.get)

    agg['상세카테고리'] = agg['UserNo'].apply(get_top_category)
    
    # 3. 위험 인원 추출 (임계치 초과)
    heavy_users = agg[agg['총다운로드'] >= config.NOTIFICATION_THRESHOLD].sort_values('총다운로드', ascending=False)
    
    if heavy_users.empty:
        return

    # 4. 중복 방지 필터링
    today_str = datetime.now().strftime("%Y-%m-%d")
    records = get_notified_records().get(today_str, {})
    
    new_risks = []
    for _, user in heavy_users.iterrows():
        u_no = str(user['UserNo'])
        last_count = records.get(u_no, 0)
        
        if user['총다운로드'] > last_count:
            new_risks.append(user)
            save_notified_record(u_no, int(user['총다운로드']))

    if not new_risks:
        return

    # 5. 이메일 발송
    new_risks_df = pd.DataFrame(new_risks)
    
    # 대표 카테고리 결정 (대표성을 위해 가장 빈도가 높은 것 선택)
    rep_cat = new_risks_df['상세카테고리'].value_counts().idxmax()
    if len(new_risks_df['상세카테고리'].unique()) > 1:
        rep_cat += " 외"
        
    date_suffix = datetime.now().strftime('%Y%m%d')
    subject = f"[EZ데이터허브] {rep_cat} 다운로드 횟수 초과 안내_{date_suffix}"
    
    html = email_utils.build_risk_alert_html(new_risks_df, config.NOTIFICATION_THRESHOLD)
    email_utils.send_email(subject, html)

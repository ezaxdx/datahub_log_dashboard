import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send_email(subject, html_content):
    """
    config.SMTP_CONFIG 설정을 사용하여 이메일을 발송합니다.
    """
    conf = config.SMTP_CONFIG
    
    if not conf.get("user") or not conf.get("password") or "@" not in conf.get("user"):
        print("[Email] SMTP 설정이 완료되지 않아 이메일을 발송하지 않습니다.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = conf["user"]
        msg['To'] = ", ".join(config.NOTIFICATION_RECIPIENTS)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(conf["host"], conf["port"]) as server:
            server.starttls()
            server.login(conf["user"], conf["password"])
            server.send_message(msg)
            
        print(f"[Email] 이메일 발신 성공: {subject}")
        return True
    except Exception as e:
        print(f"[Email] 이메일 발신 실패: {e}")
        return False

def build_risk_alert_html(risk_df, threshold):
    """
    사용자 요청 형식에 맞춰 HTML 본문을 구성합니다.
    """
    items_html = ""
    for _, row in risk_df.iterrows():
        items_html += f"""
        <div style='margin-bottom: 20px; padding: 15px; border: 1px solid #e2e8f0; border-radius: 8px;'>
            <p style='margin: 5px 0;'><b>직원 안내 :</b> {row['이름']}, ({row['부서']}/{row['직급']})</p>
            <p style='margin: 5px 0;'><b>다운로드 초과 내용 :</b> {row['상세카테고리']} {row['총다운로드']}건</p>
        </div>
        """
    
    html = f"""
    <html>
    <body style='font-family: "Malgun Gothic", sans-serif; line-height: 1.6; color: #333;'>
        <p>안녕하세요,</p>
        <p>데이터허브 다운로드 필터 조건에서 기준치(<b>{threshold}건</b>)를 초과한 직원을 안내드립니다.</p>
        <br>
        {items_html}
        <br>
        <p style='font-size: 12px; color: #64748b; border-top: 1px solid #eee; padding-top: 10px;'>
            이 메일은 시스템에 의해 자동으로 생성된 알림입니다.
        </p>
    </body>
    </html>
    """
    return html

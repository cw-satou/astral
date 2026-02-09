import os
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import json
from datetime import datetime

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

TO_ADDRESS = "cw.satou@gmail.com"

def send_order_mail(order_data: dict, diagnosis_id: str) -> bool:
    """
    オーダー確定時にメールを送信

    Args:
        order_data: オーダーサマリー情報（辞書）
        diagnosis_id: 診断ID

    Returns:
        送信成功時は True、失敗時は False
    """

    # SMTP設定がない場合はログだけ出して続行
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        print("⚠️  SMTP settings not fully configured; email not sent.")
        print(f"   Configure SMTP_HOST, SMTP_USER, SMTP_PASS in Vercel env vars")
        return False

    try:
        subject = f"【星の羅針盤】オーダー通知 #{diagnosis_id}"

        # メール本文を作成
        body = f"""星の羅針盤へのオーダーが確定しました。

【診断ID】
{diagnosis_id}

【オーダー内容】
{json.dumps(order_data, ensure_ascii=False, indent=2)}

【送信時刻】
{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}

---
星の羅針盤 - 占い×アクセサリー
"""

        # メール作成
        msg = MIMEText(body, _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = TO_ADDRESS
        msg["Date"] = formatdate(localtime=True)

        # 送信
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)

        print(f"✅ Order email sent to {TO_ADDRESS}")
        return True

    except smtplib.SMTPAuthenticationError as auth_err:
        print(f"❌ SMTP Authentication Error: {str(auth_err)}")
        return False
    except smtplib.SMTPException as smtp_err:
        print(f"❌ SMTP Error: {str(smtp_err)}")
        return False
    except Exception as e:
        print(f"❌ Mail Error: {str(e)}")
        return False
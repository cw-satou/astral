"""メール送信ユーティリティ

オーダー確定時の通知メール送信機能を提供する。
"""

import os
import smtplib
import logging
import json
from email.mime.text import MIMEText
from email.utils import formatdate
from datetime import datetime

logger = logging.getLogger(__name__)


def send_order_mail(order_data: dict, diagnosis_id: str) -> bool:
    """オーダー確定時に管理者へ通知メールを送信する

    Args:
        order_data: オーダーサマリー情報
        diagnosis_id: 診断ID

    Returns:
        送信成功時はTrue、失敗時はFalse
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    to_address = os.environ.get("ORDER_NOTIFICATION_EMAIL", "")

    if not (smtp_host and smtp_user and smtp_pass and to_address):
        logger.warning(
            "SMTP設定が不完全です（SMTP_HOST, SMTP_USER, SMTP_PASS, "
            "ORDER_NOTIFICATION_EMAIL を設定してください）"
        )
        return False

    try:
        subject = f"【星の羅針盤】オーダー通知 #{diagnosis_id}"

        body = (
            "星の羅針盤へのオーダーが確定しました。\n"
            "\n"
            f"【診断ID】\n{diagnosis_id}\n"
            "\n"
            "【オーダー内容】\n"
            f"{json.dumps(order_data, ensure_ascii=False, indent=2)}\n"
            "\n"
            "【送信時刻】\n"
            f"{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n"
            "\n"
            "---\n"
            "星の羅針盤 - 占い×アクセサリー\n"
        )

        msg = MIMEText(body, _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_address
        msg["Date"] = formatdate(localtime=True)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)

        logger.info(f"注文通知メール送信成功: to={to_address}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP認証エラー: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTPエラー: {e}")
        return False
    except Exception as e:
        logger.error(f"メール送信エラー: {e}")
        return False


def send_rate_limit_alert(ip_address: str, endpoint: str, count: int) -> bool:
    """レート制限超過時に管理者へ警告メールを送信する

    Args:
        ip_address: 超過したIPアドレス
        endpoint: 対象エンドポイント
        count: リクエスト数

    Returns:
        送信成功時はTrue、失敗時はFalse
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    to_address = os.environ.get("ORDER_NOTIFICATION_EMAIL", "")

    if not (smtp_host and smtp_user and smtp_pass and to_address):
        logger.warning("レート制限警告メール: SMTP設定が不完全です")
        return False

    try:
        subject = "【星の羅針盤】レート制限超過警告"

        body = (
            "レート制限が超過しました。\n"
            "\n"
            f"【IPアドレス】\n{ip_address}\n"
            "\n"
            f"【エンドポイント】\n{endpoint}\n"
            "\n"
            f"【リクエスト数】\n{count}回\n"
            "\n"
            "【検出時刻】\n"
            f"{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n"
            "\n"
            "※同一IPからの警告は1時間に1回までに制限されています。\n"
            "---\n"
            "星の羅針盤 - システム監視\n"
        )

        msg = MIMEText(body, _charset="utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_address
        msg["Date"] = formatdate(localtime=True)

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
            s.starttls()
            s.login(smtp_user, smtp_pass)
            s.send_message(msg)

        logger.info(f"レート制限警告メール送信成功: IP={ip_address}")
        return True

    except Exception as e:
        logger.error(f"レート制限警告メール送信エラー: {e}")
        return False

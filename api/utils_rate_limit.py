"""レート制限モジュール

IPアドレスベースのインメモリレート制限を提供する。
Vercelサーバーレス環境ではプロセスが短命なため完璧ではないが、
同一インスタンス内での連続リクエストを制限できる。
"""

import time
import logging
import threading
from collections import defaultdict
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)

# レート制限設定: エンドポイント → (最大リクエスト数, 時間ウィンドウ秒)
RATE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/diagnose": (10, 3600),        # 10回/時間
    "/api/today-fortune": (20, 3600),   # 20回/時間
    "/api/build-bracelet": (10, 3600),  # 10回/時間
}

# レート制限超過時のユーザー向けメッセージ
RATE_LIMIT_MESSAGE = (
    "只今、たくさんのご依頼をいただいており、"
    "少しお時間をいただいております。"
    "10分ほどお待ちいただいてから、もう一度お試しください。"
)

# IPごとのリクエスト記録: {endpoint: {ip: [timestamp, ...]}}
_request_log: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
# 警告メール送信記録: {ip: last_alert_timestamp}
_alert_log: dict[str, float] = {}
# スレッドセーフティ
_lock = threading.Lock()

# 警告メールの最小間隔（秒）: 同一IPにつき1時間に1回まで
ALERT_COOLDOWN = 3600


def _get_client_ip() -> str:
    """クライアントのIPアドレスを取得する"""
    # Vercelではx-forwarded-forヘッダーにクライアントIPが入る
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _cleanup_old_entries(entries: list[float], window: int) -> list[float]:
    """期限切れのエントリをクリーンアップする"""
    cutoff = time.time() - window
    return [t for t in entries if t > cutoff]


def check_rate_limit(endpoint: str) -> tuple[bool, int]:
    """レート制限をチェックする

    Args:
        endpoint: APIエンドポイントパス

    Returns:
        (制限超過フラグ, 現在のリクエスト数) のタプル
    """
    if endpoint not in RATE_LIMITS:
        return False, 0

    max_requests, window = RATE_LIMITS[endpoint]
    ip = _get_client_ip()
    now = time.time()

    with _lock:
        # 古いエントリをクリーンアップ
        _request_log[endpoint][ip] = _cleanup_old_entries(
            _request_log[endpoint][ip], window
        )
        # 現在のリクエスト数
        current_count = len(_request_log[endpoint][ip])

        if current_count >= max_requests:
            return True, current_count

        # リクエストを記録
        _request_log[endpoint][ip].append(now)
        return False, current_count + 1


def should_send_alert(ip: str) -> bool:
    """警告メールを送信すべきかチェックする（スパム防止）"""
    now = time.time()
    with _lock:
        last_alert = _alert_log.get(ip, 0)
        if now - last_alert < ALERT_COOLDOWN:
            return False
        _alert_log[ip] = now
        return True


def rate_limit_response():
    """レート制限超過時のレスポンスを返す"""
    return jsonify({
        "message": RATE_LIMIT_MESSAGE,
        "retry_after": 600,
    }), 429


def rate_limited(f):
    """レート制限デコレータ

    Flaskルートハンドラに適用して、レート制限を自動チェックする。
    制限超過時はフレンドリーなメッセージを返し、管理者にメール通知する。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        endpoint = request.path
        exceeded, count = check_rate_limit(endpoint)

        if exceeded:
            ip = _get_client_ip()
            logger.warning(
                f"レート制限超過: IP={ip}, endpoint={endpoint}, count={count}"
            )

            # 管理者への警告メール（スパム防止付き）
            if should_send_alert(ip):
                try:
                    from api.utils_mail import send_rate_limit_alert
                    send_rate_limit_alert(ip, endpoint, count)
                except Exception as e:
                    logger.error(f"レート制限警告メール送信失敗: {e}")

            return rate_limit_response()

        return f(*args, **kwargs)
    return decorated

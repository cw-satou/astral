"""レート制限モジュールの単体テスト"""

import pytest
from api.index import app
from api.utils_rate_limit import (
    check_rate_limit,
    should_send_alert,
    RATE_LIMITS,
    _request_log,
    _alert_log,
    _lock,
)


@pytest.fixture(autouse=True)
def clear_state():
    """テスト間でレート制限の状態をリセット"""
    with _lock:
        _request_log.clear()
        _alert_log.clear()
    yield
    with _lock:
        _request_log.clear()
        _alert_log.clear()


@pytest.fixture
def req_context():
    """Flaskリクエストコンテキスト"""
    with app.test_request_context(
        '/api/diagnose',
        environ_base={'REMOTE_ADDR': '1.2.3.4'},
        headers={'X-Forwarded-For': '1.2.3.4'},
    ):
        yield


class TestCheckRateLimit:
    """check_rate_limit関数のテスト"""

    def test_unknown_endpoint(self, req_context):
        """未知のエンドポイントは制限しない"""
        exceeded, count = check_rate_limit("/api/unknown")
        assert exceeded is False
        assert count == 0

    def test_within_limit(self, req_context):
        """制限内のリクエストは許可される"""
        for _ in range(5):
            exceeded, count = check_rate_limit("/api/diagnose")
            assert exceeded is False

    def test_exceeds_limit(self, req_context):
        """制限を超えたリクエストは拒否される"""
        max_requests = RATE_LIMITS["/api/diagnose"][0]
        for i in range(max_requests):
            exceeded, _ = check_rate_limit("/api/diagnose")
            assert exceeded is False

        # 次のリクエストは制限超過
        exceeded, count = check_rate_limit("/api/diagnose")
        assert exceeded is True
        assert count == max_requests

    def test_different_ips_independent(self):
        """異なるIPは独立してカウントされる"""
        # IP1で5回
        with app.test_request_context(
            '/api/diagnose',
            headers={'X-Forwarded-For': '1.1.1.1'},
        ):
            for _ in range(5):
                check_rate_limit("/api/diagnose")

        # IP2は0回からスタート
        with app.test_request_context(
            '/api/diagnose',
            headers={'X-Forwarded-For': '2.2.2.2'},
        ):
            exceeded, count = check_rate_limit("/api/diagnose")
            assert exceeded is False
            assert count == 1


class TestShouldSendAlert:
    """should_send_alert関数のテスト"""

    def test_first_alert(self):
        """初回の警告は送信可能"""
        assert should_send_alert("1.2.3.4") is True

    def test_duplicate_alert_blocked(self):
        """同一IPの連続警告はブロックされる"""
        should_send_alert("1.2.3.4")
        assert should_send_alert("1.2.3.4") is False

    def test_different_ip_allowed(self):
        """異なるIPは独立して警告可能"""
        should_send_alert("1.2.3.4")
        assert should_send_alert("5.6.7.8") is True

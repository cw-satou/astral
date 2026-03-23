"""ホロスコープ計算の統合テスト

Swiss Ephemeris（Moshier ephemeris）を使ったチャート計算の正確性を検証する。
"""

import pytest

try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False

from api.utils_perplexity import calculate_chart, get_sign, sign_element_balance


@pytest.mark.skipif(not HAS_SWISSEPH, reason="pyswisseph未インストール")
class TestCalculateChart:
    """calculate_chart: ホロスコープ計算の統合テスト"""

    def test_known_date(self):
        """既知の日付で計算が成功する"""
        # 2000年1月1日 12:00 東京
        result = calculate_chart("2000-01-01", "12:00", 35.6762, 139.6503)
        assert result is not None
        assert "sun" in result
        assert "moon" in result
        assert "asc" in result
        assert "element_balance" in result

    def test_sun_sign_january(self):
        """1月1日の太陽は山羊座"""
        result = calculate_chart("2000-01-01", "12:00", 35.6762, 139.6503)
        assert result["sun"] == "Capricorn"

    def test_sun_sign_july(self):
        """7月15日の太陽は蟹座"""
        result = calculate_chart("2000-07-15", "12:00", 35.6762, 139.6503)
        assert result["sun"] == "Cancer"

    def test_sun_sign_march_equinox(self):
        """3月21日の太陽は牡羊座付近"""
        result = calculate_chart("2000-03-21", "12:00", 35.6762, 139.6503)
        # 春分点付近なので牡羊座かうお座
        assert result["sun"] in ("Aries", "Pisces")

    def test_element_balance_valid(self):
        """エレメントバランスが有効な値を返す"""
        result = calculate_chart("1990-06-15", "10:30", 34.6937, 135.5023)
        balance = result.get("element_balance", {})
        assert sum(balance.values()) > 0
        for key in ["fire", "earth", "wind", "water"]:
            assert key in balance
            assert balance[key] >= 0

    def test_invalid_date(self):
        """不正な日付は空の辞書を返す"""
        result = calculate_chart("invalid", "12:00", 35.6762, 139.6503)
        assert result == {}

    def test_invalid_time(self):
        """不正な時刻は空の辞書を返す"""
        result = calculate_chart("2000-01-01", "invalid", 35.6762, 139.6503)
        assert result == {}

    def test_different_locations(self):
        """異なる場所でASCが変わる可能性がある"""
        tokyo = calculate_chart("2000-01-01", "12:00", 35.6762, 139.6503)
        london = calculate_chart("2000-01-01", "12:00", 51.5074, -0.1278)
        # 太陽は同じだがASCは異なるはず
        assert tokyo["sun"] == london["sun"]
        # ASCは場所依存なので異なる可能性が高い（ただし保証はしない）

    def test_historical_date(self):
        """過去の日付でも計算できる"""
        result = calculate_chart("1950-01-01", "00:00", 35.6762, 139.6503)
        assert result is not None
        assert "sun" in result

    def test_recent_date(self):
        """最近の日付でも計算できる"""
        result = calculate_chart("2024-01-01", "12:00", 35.6762, 139.6503)
        assert result is not None
        assert "sun" in result

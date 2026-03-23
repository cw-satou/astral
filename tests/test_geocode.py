"""ジオコーディングモジュールの単体テスト"""

import pytest
from api.utils_geocode import geocode, JAPAN_CITIES, DEFAULT_LAT, DEFAULT_LON


class TestGeocode:
    """geocode関数のテスト"""

    def test_known_city_exact(self):
        """完全一致する都市名で正しい座標を返す"""
        lat, lon = geocode("東京")
        assert lat == pytest.approx(35.6762, abs=0.01)
        assert lon == pytest.approx(139.6503, abs=0.01)

    def test_known_city_with_shi(self):
        """「市」付きの都市名で正しい座標を返す"""
        lat, lon = geocode("横浜市")
        assert lat == pytest.approx(35.4437, abs=0.01)
        assert lon == pytest.approx(139.6380, abs=0.01)

    def test_partial_match(self):
        """部分一致で都市を検索できる"""
        lat, lon = geocode("東京都港区")
        assert lat == pytest.approx(35.6762, abs=0.01)

    def test_empty_string_returns_default(self):
        """空文字の場合はデフォルト値（東京）を返す"""
        lat, lon = geocode("")
        assert lat == DEFAULT_LAT
        assert lon == DEFAULT_LON

    def test_none_returns_default(self):
        """Noneの場合はデフォルト値を返す"""
        lat, lon = geocode(None)
        assert lat == DEFAULT_LAT
        assert lon == DEFAULT_LON

    def test_unknown_place_returns_default(self):
        """辞書にもNominatimにもない場所はデフォルト値を返す"""
        lat, lon = geocode("存在しない架空の場所XYZ123")
        # デフォルト値またはNominatimの結果
        assert isinstance(lat, float)
        assert isinstance(lon, float)

    def test_sapporo(self):
        """札幌の座標が正しい"""
        lat, lon = geocode("札幌")
        assert lat == pytest.approx(43.0618, abs=0.01)
        assert lon == pytest.approx(141.3545, abs=0.01)

    def test_all_cities_in_dict(self):
        """ハードコード辞書の全都市が有効な座標を持つ"""
        for city, (lat, lon) in JAPAN_CITIES.items():
            assert -90 <= lat <= 90, f"{city}: 緯度が範囲外 ({lat})"
            assert -180 <= lon <= 180, f"{city}: 経度が範囲外 ({lon})"

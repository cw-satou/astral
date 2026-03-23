"""診断モジュールの単体テスト"""

import pytest
from api.diagnose import (
    get_birthstone_from_birth,
    ELEMENT_STONE_MAP,
    STONE_PRODUCT_MAP,
    BIRTHSTONE_MAP,
)


class TestGetBirthstoneFromBirth:
    """get_birthstone_from_birth: 誕生石判定"""

    def test_january(self):
        result = get_birthstone_from_birth({"date": "1990-01-15"})
        assert result["name"] == "ガーネット"
        assert "1月" in result["reason"]

    def test_february(self):
        result = get_birthstone_from_birth({"date": "1985-02-28"})
        assert result["name"] == "アメジスト"

    def test_december(self):
        result = get_birthstone_from_birth({"date": "2000-12-25"})
        assert result["name"] == "ターコイズ"

    def test_no_date(self):
        result = get_birthstone_from_birth({})
        assert result["name"] == "水晶"

    def test_none_input(self):
        result = get_birthstone_from_birth(None)
        assert result["name"] == "水晶"

    def test_invalid_date(self):
        result = get_birthstone_from_birth({"date": "invalid"})
        assert result["name"] == "水晶"

    def test_all_months_covered(self):
        """全12ヶ月の誕生石が定義されている"""
        for month in range(1, 13):
            assert month in BIRTHSTONE_MAP


class TestMappings:
    """マッピングテーブルの整合性テスト"""

    def test_element_stone_map_covers_all(self):
        """全エレメントに対応する石がある"""
        for element in ["火", "地", "風", "水"]:
            assert element in ELEMENT_STONE_MAP

    def test_stone_product_map_covers_element_stones(self):
        """エレメント石に対応する商品がある"""
        for stone in ELEMENT_STONE_MAP.values():
            assert stone in STONE_PRODUCT_MAP

    def test_product_slugs_format(self):
        """商品スラッグがtop-で始まる"""
        for slug in STONE_PRODUCT_MAP.values():
            assert slug.startswith("top-")

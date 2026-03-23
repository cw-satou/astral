"""Perplexity AIユーティリティの単体テスト

外部API呼び出しなしで、計算ロジックや石選定ロジックをテストする。
"""

import pytest
from api.utils_perplexity import (
    get_sign,
    sign_element_balance,
    weakest_element,
    build_chart_data,
    choose_main_stones,
    choose_sub_stones,
    choose_products,
    choose_theme,
    _strip_code_block,
    _clean_citations,
    SIGNS,
    ELEMENT_MAP,
    STOCK_STONES,
)


class TestGetSign:
    """get_sign: 黄経から星座判定"""

    def test_aries_start(self):
        assert get_sign(0.0) == "Aries"

    def test_aries_end(self):
        assert get_sign(29.9) == "Aries"

    def test_taurus(self):
        assert get_sign(30.0) == "Taurus"

    def test_gemini(self):
        assert get_sign(65.0) == "Gemini"

    def test_pisces(self):
        assert get_sign(350.0) == "Pisces"

    def test_wrap_around(self):
        """360度以上はモジュロ処理される"""
        assert get_sign(360.0) == "Aries"
        # 390.0 / 30 = 13, 13 % 12 = 1 → Taurus
        assert get_sign(390.0) == "Taurus"

    def test_all_signs_reachable(self):
        """各星座が30度間隔で到達可能"""
        for i, sign in enumerate(SIGNS):
            assert get_sign(i * 30 + 15) == sign


class TestSignElementBalance:
    """sign_element_balance: エレメントバランス計算"""

    def test_balanced(self):
        signs = {
            "sun": "Aries",     # fire
            "moon": "Taurus",   # earth
            "asc": "Gemini",    # wind
            "mercury": "Cancer", # water
        }
        balance = sign_element_balance(signs)
        assert balance == {"fire": 1, "earth": 1, "wind": 1, "water": 1}

    def test_fire_dominant(self):
        signs = {
            "sun": "Aries",
            "moon": "Leo",
            "asc": "Sagittarius",
            "mercury": "Cancer",
        }
        balance = sign_element_balance(signs)
        assert balance["fire"] == 3
        assert balance["water"] == 1

    def test_empty(self):
        balance = sign_element_balance({})
        assert balance == {"fire": 0, "earth": 0, "wind": 0, "water": 0}


class TestWeakestElement:
    """weakest_element: 最弱エレメント判定"""

    def test_water_weakest(self):
        balance = {"fire": 3, "earth": 2, "wind": 1, "water": 0}
        assert weakest_element(balance) == "water"

    def test_tie_returns_first(self):
        balance = {"fire": 1, "earth": 1, "wind": 0, "water": 0}
        result = weakest_element(balance)
        assert result in ("wind", "water")


class TestBuildChartData:
    """build_chart_data: チャートデータ構築"""

    def test_default_values(self):
        data = build_chart_data()
        assert "sun" in data
        assert "moon" in data
        assert "asc" in data
        assert "sun_ja" in data
        assert "element_lack" in data
        assert "element_lack_ja" in data

    def test_with_chart_data(self):
        chart = {
            "sun": "Leo",
            "moon": "Aries",
            "asc": "Scorpio",
            "mercury": "Virgo",
            "venus": "Libra",
            "mars": "Capricorn",
            "element_balance": {"fire": 2, "earth": 2, "wind": 1, "water": 1},
        }
        data = build_chart_data(chart_data=chart)
        assert data["sun"] == "Leo"
        assert data["sun_ja"] == "獅子座"
        assert data["asc_ja"] == "蠍座"


class TestChooseMainStones:
    """choose_main_stones: AI石選定→在庫照合"""

    def test_valid_stone(self):
        ai_stones = [{"name": "ラピスラズリ", "reason": "テスト"}]
        result = choose_main_stones(ai_stones)
        assert len(result) >= 1
        assert result[0]["name"] == "ラピスラズリ"

    def test_invalid_stone_fallback(self):
        ai_stones = [{"name": "存在しない石", "reason": "テスト"}]
        result = choose_main_stones(ai_stones)
        assert len(result) == 1
        assert result[0]["name"] == "ラピスラズリ"  # フォールバック

    def test_sub_stone_excluded(self):
        """サブ石（role=sub）はメイン石に選ばれない"""
        ai_stones = [{"name": "グレークォーツ", "reason": "テスト"}]
        result = choose_main_stones(ai_stones)
        assert result[0]["name"] == "ラピスラズリ"  # フォールバック

    def test_max_two_stones(self):
        ai_stones = [
            {"name": "ラピスラズリ", "reason": "1"},
            {"name": "アメジスト", "reason": "2"},
            {"name": "マラカイト", "reason": "3"},
        ]
        result = choose_main_stones(ai_stones)
        assert len(result) <= 2


class TestChooseSubStones:
    """choose_sub_stones: メイン石からサブ石選定"""

    def test_blue_main(self):
        main = [{"name": "ラピスラズリ", "color": "blue"}]
        subs = choose_sub_stones(main)
        assert len(subs) > 0
        sub_names = [s["name"] for s in subs]
        assert any(n in ["シーブルーカルセドニー", "グレークォーツ"] for n in sub_names)

    def test_max_two_subs(self):
        main = [{"name": "アメジスト", "color": "purple"}]
        subs = choose_sub_stones(main)
        assert len(subs) <= 2


class TestChooseProducts:
    """choose_products: 商品マッピング"""

    def test_basic_product(self):
        main = "ラピスラズリ"
        subs = [{"name": "グレークォーツ"}]
        products = choose_products(main, subs)
        assert len(products) > 0
        slugs = [p["slug"] for p in products]
        assert any("lapis" in s for s in slugs)


class TestChooseTheme:
    """choose_theme: 悩みカテゴリ→テーマ変換"""

    def test_love(self):
        assert choose_theme(["恋愛"]) == "love"

    def test_work(self):
        assert choose_theme(["仕事"]) == "action"

    def test_health(self):
        assert choose_theme(["健康"]) == "heal"

    def test_empty(self):
        assert choose_theme([]) == "heal"

    def test_unknown(self):
        assert choose_theme(["その他"]) == "heal"


class TestStripCodeBlock:
    """_strip_code_block: コードブロック除去"""

    def test_json_block(self):
        text = '```json\n{"key": "value"}\n```'
        assert _strip_code_block(text) == '{"key": "value"}'

    def test_plain_block(self):
        text = '```\nplain text\n```'
        assert _strip_code_block(text) == 'plain text'

    def test_no_block(self):
        text = 'just plain text'
        assert _strip_code_block(text) == 'just plain text'


class TestCleanCitations:
    """_clean_citations: 引用表記除去"""

    def test_remove_citations(self):
        text = "これは[1]テスト[2]です[10]"
        assert _clean_citations(text) == "これはテストです"

    def test_no_citations(self):
        text = "引用なしのテキスト"
        assert _clean_citations(text) == "引用なしのテキスト"

"""Perplexity AI連携モジュール

占い診断のAI鑑定、ホロスコープ計算、石の選定ロジックを提供する。
Perplexity API（OpenAI互換）を使用して、ユーザーの出生情報と悩みから
パーソナライズされた鑑定結果を生成する。
"""

import os
import json
import re
import random
import logging
import swisseph as swe
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)

# ===== API クライアント =====

PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")


def _get_client() -> OpenAI | None:
    """Perplexity APIクライアントを取得する（遅延初期化）"""
    if not PERPLEXITY_API_KEY:
        return None
    return OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai",
    )


# ===== 商品マッピング =====

PRODUCT_BY_MAIN_STONE = {
    "ラピスラズリ": {"id": 1203, "slug": "bracelet-lapis-gray"},
    "カーネリアン・サードニクス": {"id": 1204, "slug": "bracelet-carnelian-gray"},
    "マラカイト": {"id": 1205, "slug": "bracelet-malachite-gray"},
    "アメジスト": {"id": 1206, "slug": "bracelet-amethyst-gray"},
}

LIMITED_PRODUCTS = {
    "ラピスラズリ": {"id": 1207, "slug": "bracelet-iris-lapis-gray"},
    "カーネリアン・サードニクス": {"id": 1208, "slug": "bracelet-iris-carnelian-gray"},
    "マラカイト": {"id": 1209, "slug": "bracelet-iris-malachite-gray"},
    "アメジスト": {"id": 1210, "slug": "bracelet-iris-amethyst-gray"},
}

COLOR_PRODUCTS = {
    "マダガスカル産ローズクォーツ": {"id": 1202, "slug": "bracelet-yasashiitsuki"},
    "シーブルーカルセドニー": {"id": 1201, "slug": "bracelet-shizukanaumi"},
}

# ===== 星座・エレメント定義 =====

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ELEMENT_MAP = {
    "Aries": "fire", "Leo": "fire", "Sagittarius": "fire",
    "Taurus": "earth", "Virgo": "earth", "Capricorn": "earth",
    "Gemini": "wind", "Libra": "wind", "Aquarius": "wind",
    "Cancer": "water", "Scorpio": "water", "Pisces": "water",
}

SIGN_JA = {
    "Aries": "牡羊座", "Taurus": "牡牛座", "Gemini": "双子座",
    "Cancer": "蟹座", "Leo": "獅子座", "Virgo": "乙女座",
    "Libra": "天秤座", "Scorpio": "蠍座", "Sagittarius": "射手座",
    "Capricorn": "山羊座", "Aquarius": "水瓶座", "Pisces": "魚座",
}

ELEMENT_JA = {
    "fire": "火", "earth": "地", "wind": "風", "water": "水",
}

# ===== オラクルカード定義 =====

ORACLE_CARDS = [
    {
        "name": "豊かさの扉",
        "en": "abundance door with golden light",
        "meaning_up": "豊かさへの流れが開く・受け取る準備ができている",
        "meaning_rev": "受け取ることへの抵抗・自己制限のパターン",
    },
    {
        "name": "変容の炎",
        "en": "transformation flame rising from darkness",
        "meaning_up": "変化を受け入れることで新しい自分へ",
        "meaning_rev": "変化への恐れ・現状への執着",
    },
    {
        "name": "愛と調和",
        "en": "heart of light surrounded by blooming flowers",
        "meaning_up": "愛のエネルギーが満ちている・関係性の調和",
        "meaning_rev": "自己愛の不足・感情の閉じ込め",
    },
    {
        "name": "手放しの風",
        "en": "wind releasing white feathers into sky",
        "meaning_up": "手放すことで軽くなる・執着からの解放",
        "meaning_rev": "手放せない何か・過去への引き戻し",
    },
    {
        "name": "内なる声",
        "en": "glowing compass in a quiet moonlit forest",
        "meaning_up": "直感を信じるとき・内側からの答え",
        "meaning_rev": "外の声に振り回されている・自分を見失いかけている",
    },
    {
        "name": "勇気の一歩",
        "en": "lone figure stepping forward into dawn light",
        "meaning_up": "踏み出す力がある・恐れを超えた先に道がある",
        "meaning_rev": "迷いで足が止まっている・自信の喪失",
    },
    {
        "name": "癒しの泉",
        "en": "serene healing spring in an enchanted forest",
        "meaning_up": "心と体の回復期・癒しを受け取る",
        "meaning_rev": "疲れを無視している・休息への抵抗",
    },
    {
        "name": "新しい夜明け",
        "en": "sunrise over mountains with rainbow light",
        "meaning_up": "新しい始まりの予兆・リセットの時",
        "meaning_rev": "古いパターンへの固執・過去を引きずっている",
    },
    {
        "name": "守護の翼",
        "en": "angelic wings of light protecting from above",
        "meaning_up": "守られている・見えないサポートがある",
        "meaning_rev": "孤立感・信頼できるものを探している",
    },
    {
        "name": "静寂の知恵",
        "en": "ancient tree with roots of starlight in silent night",
        "meaning_up": "立ち止まって内省するとき・答えは内側にある",
        "meaning_rev": "焦りで判断が曇っている・冷静さを取り戻す必要",
    },
    {
        "name": "つながりの光",
        "en": "golden threads connecting stars in the cosmos",
        "meaning_up": "大切なつながりが育っている・縁の深まり",
        "meaning_rev": "孤独感・本当のつながりへの渇望",
    },
    {
        "name": "創造の種",
        "en": "seed of light sprouting from dark soil into radiance",
        "meaning_up": "創造力が湧いている・アイデアを形にするとき",
        "meaning_rev": "表現への恐れ・才能を隠している",
    },
    {
        "name": "信頼と委ね",
        "en": "leaf floating peacefully on a mirror lake",
        "meaning_up": "流れに委ねることで進む・宇宙への信頼",
        "meaning_rev": "コントロールへの執着・手放せない力み",
    },
    {
        "name": "希望の星",
        "en": "single star shining brightly through storm clouds",
        "meaning_up": "どんな状況でも光はある・希望を持ち続ける",
        "meaning_rev": "希望を見失いかけている・暗闇の中にいる",
    },
    {
        "name": "自己愛の鏡",
        "en": "luminous mirror reflecting inner beauty and light",
        "meaning_up": "自分を愛することが最初の一歩・価値に気づく",
        "meaning_rev": "自己批判・自分を後回しにしている",
    },
]

# 後方互換性のためエイリアス
CRYSTAL_ORACLE_CARDS = ORACLE_CARDS

# ===== 在庫石データ =====

STOCK_STONES = {
    "ラピスラズリ": {"size": 10, "code": "G516-6H785", "role": "main", "color": "blue"},
    "カーネリアン・サードニクス": {"size": 10, "code": "G1096-H9127", "role": "main", "color": "orange"},
    "マラカイト": {"size": 10, "code": "N294-MCT10", "role": "main", "color": "green"},
    "アイリスクォーツ": {"size": 12, "code": "N780-7283M", "role": "main", "color": "clear"},
    "アメジスト": {"size": 10, "code": "N477-8824X", "role": "main", "color": "purple"},
    "シーブルーカルセドニー": {"size": 8, "code": "CC359-01RA/#1", "role": "sub", "color": "light_blue"},
    "マダガスカル産ローズクォーツ": {"size": 8, "code": "N560-V4534", "role": "sub", "color": "pink"},
    "グレークォーツ": {"size": 10, "code": "G264-3836G", "role": "sub", "color": "gray"},
}

MAIN_TO_SUB_MAP = {
    "purple": ["マダガスカル産ローズクォーツ", "シーブルーカルセドニー", "グレークォーツ"],
    "blue": ["シーブルーカルセドニー", "グレークォーツ"],
    "orange": ["マダガスカル産ローズクォーツ", "グレークォーツ"],
    "green": ["シーブルーカルセドニー", "グレークォーツ"],
    "clear": ["マダガスカル産ローズクォーツ", "シーブルーカルセドニー", "グレークォーツ"],
    "gray": ["マダガスカル産ローズクォーツ", "シーブルーカルセドニー"],
}

SELECTABLE_STONES = "\n".join([
    "- ラピスラズリ",
    "- カーネリアン・サードニクス",
    "- マラカイト",
    "- アメジスト",
    "- アイリスクォーツ",
])

# ===== プロンプト定義 =====

SYSTEM_PROMPT = f"""
【絶対ルール】
1. 出力はすべて日本語のみ。英語は一切使用禁止。
   • 星座名: Gemini→双子座、Aries→牡羊座 のように日本語に変換
   • エレメント: fire→火、earth→地、wind→風、water→水
   • その他あらゆる英単語も日本語に置き換えてください
2. JSON形式のみを出力。Markdownのコードブロックや引用表記([1]など)は不要。
3. 【】のような見出しマークは使わず、自然な文章で書く。
4. 重要な言葉は**で囲って強調。
5. 「。」の後には改行を2つ入れる。
6. 分かりやすく、具体的で、読んだ人が「自分のことだ」と感じられる言葉で書く。
7. 神秘的・占い師的な言い回しは避け、パーソナル診断レポートとして読めるトーンにする。
   例：「運命が〜」→「あなたの傾向として〜」／「星が告げる」→「この配置から読み取れるのは」
8. 各セクションは指定文字数を目安に、現状分析と具体的なアドバイスをバランスよく。

【重要なルール】
選べる天然石は必ず以下のいずれか1つにしてください。
それ以外の石（例：水晶、クリスタル等）は絶対に選ばないでください。
"""


# ===== ホロスコープ計算 =====

# Swiss Ephemeris のデータパス設定
# swe.set_ephe_path(None) はビルトインのMoshier ephemerisを使用する。
# Moshier ephemerisは外部データファイル不要で、Vercelサーバーレス環境でも動作する。
# 精度はSwiss Ephemeris本体（約0.001秒角）より劣るが、
# 占星術の実用上十分な精度（約0.1秒角）を持つ。
swe.set_ephe_path(None)


def calculate_chart(date: str, time: str, lat: float, lon: float) -> dict:
    """出生情報から惑星の黄経を計算し、星座とエレメントバランスを返す

    Swiss Ephemeris（pyswisseph）を使用してホロスコープチャートを計算する。
    Swiss Ephemerisは天文学的に正確な惑星位置計算ライブラリで、
    指定された日時・場所から各惑星の黄道上の位置（黄経）を算出する。

    ビルトインのMoshier ephemerisを使用するため、外部データファイルは不要。

    Args:
        date: 生年月日（"YYYY-MM-DD"形式）
        time: 出生時間（"HH:MM"形式）
        lat: 出生地の緯度
        lon: 出生地の経度

    Returns:
        星座配置とエレメントバランスを含む辞書
    """
    try:
        dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        logger.warning(f"日時パースエラー: date={date}, time={time}")
        return {}

    # ユリウス日の計算（天文計算の基準日時）
    jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)

    planets = {
        "sun": swe.SUN,
        "moon": swe.MOON,
        "mercury": swe.MERCURY,
        "venus": swe.VENUS,
        "mars": swe.MARS,
    }

    # 各惑星の黄経を計算し、星座を判定
    positions = {}
    signs = {}
    for name, planet_id in planets.items():
        try:
            result = swe.calc_ut(jd, planet_id)
            longitude = result[0][0]  # 黄経（度）
            positions[name] = longitude
            signs[name] = get_sign(longitude)
        except Exception as e:
            logger.warning(f"惑星計算エラー ({name}): {e}")
            signs[name] = _DEFAULT_CHART.get(name, "Aries")

    # ASC（アセンダント）の計算
    try:
        houses = swe.houses(jd, lat, lon, b'P')  # Placidusハウスシステム
        asc_degree = houses[1][0]  # ASCの黄経
        asc_sign = get_sign(asc_degree)
    except Exception as e:
        logger.warning(f"ASC計算エラー: {e}")
        asc_sign = _DEFAULT_CHART.get("asc", "Cancer")

    # エレメントバランスの計算
    all_signs = {**signs, "asc": asc_sign}
    balance = sign_element_balance(all_signs)

    return {
        "sun": signs.get("sun", "Aries"),
        "moon": signs.get("moon", "Aries"),
        "mercury": signs.get("mercury", "Aries"),
        "venus": signs.get("venus", "Aries"),
        "mars": signs.get("mars", "Aries"),
        "asc": asc_sign,
        "element_balance": balance,
    }


def get_sign(deg: float) -> str:
    """黄経（度数）から星座名を返す"""
    return SIGNS[int(deg / 30) % 12]


def sign_element_balance(signs: dict) -> dict:
    """星座配分から4エレメントのバランスを算出する"""
    count = {"fire": 0, "earth": 0, "wind": 0, "water": 0}
    for s in signs.values():
        if s in ELEMENT_MAP:
            count[ELEMENT_MAP[s]] += 1
    return count


def weakest_element(balance: dict) -> str:
    """最も弱いエレメントを返す"""
    return min(balance, key=balance.get)


# ===== チャートデータ構築 =====

# デフォルトのチャートデータ（出生情報が不明な場合のフォールバック）
_DEFAULT_CHART = {
    "sun": "Gemini", "moon": "Pisces", "asc": "Cancer",
    "mercury": "Taurus", "venus": "Cancer", "mars": "Leo",
    "element_balance": {"fire": 1, "earth": 1, "wind": 2, "water": 2},
}


def build_chart_data(user_input: dict = None, chart_data: dict = None) -> dict:
    """ホロスコープチャートデータを構築する

    実際のチャート計算結果があればそれを使い、なければデフォルト値で補完する。
    """
    base = chart_data or {
        "sun": _DEFAULT_CHART["sun"],
        "moon": _DEFAULT_CHART["moon"],
        "asc": _DEFAULT_CHART["asc"],
        "mercury": _DEFAULT_CHART["mercury"],
        "venus": _DEFAULT_CHART["venus"],
        "mars": _DEFAULT_CHART["mars"],
        "element_balance": _DEFAULT_CHART.get("element_balance", {}),
    }

    balance = base.get("element_balance", {})
    fire = balance.get("fire", 1)
    earth = balance.get("earth", 1)
    wind = balance.get("wind", 1)
    water = balance.get("water", 1)

    element_lack = base.get("element_lack")
    if not element_lack:
        element_lack = weakest_element({
            "fire": fire, "earth": earth, "wind": wind, "water": water,
        })

    sun = base.get("sun", "Gemini")
    moon = base.get("moon", "Pisces")
    asc = base.get("asc", "Cancer")
    mercury = base.get("mercury", "Taurus")
    venus = base.get("venus", "Cancer")
    mars = base.get("mars", "Leo")

    return {
        "sun": sun, "moon": moon, "asc": asc,
        "mercury": mercury, "venus": venus, "mars": mars,
        "fire": fire, "earth": earth, "wind": wind, "water": water,
        "element_lack": element_lack,
        "sun_ja": SIGN_JA.get(sun, sun),
        "moon_ja": SIGN_JA.get(moon, moon),
        "asc_ja": SIGN_JA.get(asc, asc),
        "mercury_ja": SIGN_JA.get(mercury, mercury),
        "venus_ja": SIGN_JA.get(venus, venus),
        "mars_ja": SIGN_JA.get(mars, mars),
        "element_lack_ja": ELEMENT_JA.get(element_lack, element_lack),
    }


# ===== 商品選定 =====

def choose_products(main_stone: str, sub_stones: list) -> list:
    """メイン石とサブ石から購入候補の商品リストを生成する"""
    products = []

    base = PRODUCT_BY_MAIN_STONE.get(main_stone)
    if base:
        products.append(base)

    # サブ石にグレークォーツがあればアイリスシリーズも追加
    has_gray = any(s["name"] == "グレークォーツ" for s in sub_stones)
    if has_gray:
        limited = LIMITED_PRODUCTS.get(main_stone)
        if limited:
            products.append(limited)

    # サブ石にローズ or シーブルーがあれば色系商品も追加
    for s in sub_stones:
        color_prod = COLOR_PRODUCTS.get(s["name"])
        if color_prod and color_prod not in products:
            products.append(color_prod)

    return products


# ===== テーマ選定 =====

def choose_theme(concerns: list) -> str:
    """悩みカテゴリからテーマを決定する"""
    if not concerns:
        return "heal"

    concern_theme_map = {
        "恋愛": "love",
        "仕事": "action",
        "金運": "action",
        "健康": "heal",
        "人間関係": "intuition",
    }

    for concern, theme in concern_theme_map.items():
        if concern in concerns:
            return theme

    return "heal"


# ===== 石選定 =====

def choose_main_stones(ai_stones: list) -> list:
    """AIが選んだ石を在庫データと照合し、メイン石リストを返す"""
    matched = []
    for s in ai_stones:
        name = s.get("name", "")
        if name in STOCK_STONES and STOCK_STONES[name]["role"] == "main":
            matched.append({
                "name": name,
                **STOCK_STONES[name],
                "reason": s.get("reason", ""),
            })

    if not matched:
        fallback_name = "ラピスラズリ"
        info = STOCK_STONES[fallback_name]
        matched = [{
            "name": fallback_name,
            **info,
            "reason": "運命と真実を導く守護石としてラピスラズリが選ばれました。",
        }]

    return matched[:2]


def choose_sub_stones(main_stones: list) -> list:
    """メイン石の色相性に基づいてサブ石を選定する"""
    seen = {}
    for m in main_stones:
        color = m.get("color", "")
        for sub_name in MAIN_TO_SUB_MAP.get(color, []):
            if sub_name not in seen:
                info = STOCK_STONES[sub_name]
                seen[sub_name] = {
                    "name": sub_name,
                    **info,
                    "reason": f"{m['name']}との色合いの相性を整えるために選びました。",
                }

    return list(seen.values())[:2]


# ===== AIレスポンスのパース =====

def _strip_code_block(content: str) -> str:
    """AIレスポンスからMarkdownコードブロックを除去する"""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    return content


def _clean_citations(content: str) -> str:
    """引用表記 [1] [2] などを除去する"""
    return re.sub(r"\[\d+\]", "", content)


# ===== プロンプト構築 =====

def build_common_user_context(
    user_input: dict, chart_data: dict = None, oracle_result: dict = None
) -> str:
    """共通のユーザー情報コンテキストを構築する"""
    birth = user_input.get("birth", {})
    concerns = user_input.get("concerns", [])
    problem_text = user_input.get("problem", "")
    concerns_text = "、".join(concerns) if concerns else "指定なし"

    cd = build_chart_data(user_input, chart_data)

    oracle_text = ""
    if oracle_result:
        position_str = "正位置" if oracle_result["is_upright"] else "逆位置"
        oracle_text = (
            f"\n\n【オラクルカード結果】\n"
            f"カード: {oracle_result['card']['name']}\n"
            f"状態: {position_str}\n"
            f"意味: {oracle_result['meaning']}"
        )

    return f"""
【ユーザー情報】
性別: {user_input.get('gender', '指定なし')}
悩みカテゴリ: {concerns_text}

具体的な悩み:
{problem_text if problem_text else '指定なし'}

生年月日: {birth.get('date', '不明')}
出生時間: {birth.get('time', '不明')}
出生地: {birth.get('place', '不明')}

【石の候補】
{SELECTABLE_STONES}

※水晶は特別な石です。
人生の転換期や強い浄化が必要な場合のみ選択してください。

【ホロスコープ分析】
太陽星座: {cd['sun_ja']}
月星座: {cd['moon_ja']}
アセンダント（上昇宮）: {cd['asc_ja']}
水星: {cd['mercury_ja']}
金星: {cd['venus_ja']}
火星: {cd['mars_ja']}

エレメントバランス
火:{cd['fire']}  地:{cd['earth']}  風:{cd['wind']}  水:{cd['water']}

不足エレメント: {cd['element_lack_ja']}
{oracle_text}
"""


def create_today_fortune_prompt(user_input: dict, chart_data: dict = None) -> str:
    """今日の運勢用プロンプトを構築する"""
    common_context = build_common_user_context(
        user_input=user_input,
        chart_data=chart_data,
        oracle_result=None,
    )

    return f"""
以下の情報をもとに、今日一日のエネルギー傾向と過ごし方のヒントを日本語で1メッセージだけ生成してください。

あなたは、西洋占星術と天然石の特性に詳しいパーソナルアドバイザーです。
神秘的・占い的な表現は避け、「今のあなたの状態」を分かりやすく分析するように伝えてください。

{common_context}

【出力条件】
- メッセージ本文だけを返してください
- JSON不要、コードブロック不要
- 3段落で構成
- 各段落は3〜5行以内
- 今日の傾向、行動のコツ、気持ちの整え方を含める
- 「今日のあなたは…」のような自然な導入を含める
- 前向きで具体的な内容にする
"""


def create_user_prompt(
    user_input: dict, oracle_result: dict, chart_data: dict = None
) -> str:
    """メイン診断用のユーザープロンプトを構築する"""
    common_context = build_common_user_context(
        user_input=user_input,
        chart_data=chart_data,
        oracle_result=oracle_result,
    )

    position_str = "正位置" if oracle_result["is_upright"] else "逆位置"

    concerns = user_input.get("concerns", [])
    concerns_text = "、".join(concerns) if concerns else "全体運"
    problem_text = (user_input.get("problem") or "").strip()

    # ユーザーが具体的な悩みを書いている場合は、それを最優先で扱う
    if problem_text:
        problem_instruction = f"""
【最重要】ユーザーが自分の言葉で書いた悩み:
「{problem_text}」

この一文一文に込められた感情・状況・言葉を最大限くみ取ってください。
すべてのセクションで、この悩みに直接応えるように語りかけること。
ホロスコープはこの悩みを読み解くための「補足」として使い、
あくまでユーザーの悩みが鑑定の中心軸です。
"""
    else:
        problem_instruction = f"今回のユーザーの悩みカテゴリは「{concerns_text}」です。すべてのセクションで、この悩みに沿った場面や感情を交えてください。"

    return f"""
以下の情報をもとに、パーソナル診断レポートを作成してください。

あなたは西洋占星術と天然石の特性に詳しいパーソナルアドバイザーです。
神秘的・占い的な表現は使わず、読んだ人が「自分の傾向が分かった」と感じられる
具体的で分かりやすい言葉で書いてください。

{problem_instruction}

{common_context}

【文体のルール】
- 占術用語・英語略語は使わない（「トランジット」「ハウス」「アセンダント」「MC」「IC」など禁止）
- 「運命」「宿命」「星が示す」などのスピリチュアル表現は避ける
- 「〜な傾向があります」「〜しやすい時期です」など分析・診断的な言い回しを使う
- ユーザーの悩みに出てくる具体的な言葉・場面・感情をそのまま拾って使う
- 1文を短くし、読んでいて息苦しくない長さにする
- 「〜です。\n\n」のように句点後は改行を2つ入れる

【出力JSONスキーマ】
{{
"destiny_map": "ホロスコープ配置から読み取れる、生まれ持った気質と今後向いている方向性を250文字程度で。「あなたの星座バランスから見えてくるのは、〜という傾向です」のように分析口調で始める。ユーザーの悩みとの関連を含める。",
"past": "これまでのユーザーの行動パターンや強みを150文字程度で。「これまでのあなたは〜という特性を持っています」のように特性を整理する。ユーザーの悩みに関連する強みを含める。",
"present_future": "今の状態と、これからの変化の方向性を200文字程度で。「いまのあなたは〜という状態にあります」と現状を整理し、「〜を意識することで」と具体的な行動につながるヒントを伝える。ユーザーの悩みに直接沿って書く。",
"element_diagnosis": "星座バランスから分かるエネルギーの偏りを150文字程度で。「最近、〇〇な気持ちになることはありませんか？」と問いかけてから、バランスの特徴を説明する。ユーザーの悩みに絡めた具体例を1つ入れる。",
"oracle_message": "引いたカード「{oracle_result['card']['name']}」の{position_str}が示すヒントを150文字程度で。「このカードが示すのは〜ということです」と、今のあなたへの示唆として伝える。ユーザーの悩みへの気づきにつなげる。",
"bracelet_proposal": "今のあなたに必要な石のエネルギーを日常に取り入れることで期待できる変化を150文字程度で。ユーザーの悩みに関連する具体的な場面（例：「〜で困っているとき、石を身につけることで」）を描く。",
"stone_support_message": "今のあなたに必要な石のエネルギー特性がユーザーの現状にどう作用するかを200文字程度で。不足エレメントを補う石の性質と、それがどうユーザーの状況に働きかけるかを具体的に説明する。",
"daily_advice": "今日からできる具体的なアクションを3つ、それぞれ25文字以内で。カンマ区切り。ユーザーの悩みに関連する実践的な行動を含める。",
"lucky_color": "今日意識するとよいカラー（1色、日本語）",
"affirmation": "自己肯定のひと言を50文字程度で。「私は…」で始める。ユーザーの悩みに関連した前向きな言葉にする。",
"element": "ユーザーに必要なエレメント（火/地/風/水）",
"theme": "テーマ（恋愛/癒し/行動/直感）",
"theme_weights": {{
  "テーマタグ（下記から選んで重みを付ける）": 0.0〜1.0,
  "使えるタグ例：行動力、情熱、創造性、自己表現、愛情、調和、自己愛、癒し、変容、前進、保護、直感、真実、知性、安定、浄化、再生、勇気": 0.0
}},
"worry_weights": {{
  "悩みタグ（下記から選んで重みを付ける）": 0.0〜1.0,
  "使えるタグ例：仕事、恋愛、人間関係、金運、健康、迷い、不安、自信不足、停滞感、感情の揺れ、踏み出せない、変化への恐れ、孤独感、疲れ": 0.0
}}
}}

theme_weights・worry_weights はユーザーの状況に当てはまるタグだけを含め、関係ないタグは省略する。
必ずJSON形式のみで出力。JSON以外のテキストや説明は一切不要。
英語が一文字でも含まれていたらやり直し。
"""


# ===== 今日の運勢生成 =====

def generate_today_fortune(user_input: dict, chart_data: dict = None) -> str:
    """今日の運勢テキストを生成する

    APIが利用できない場合はフォールバックメッセージを返す。
    """
    client = _get_client()
    if not client:
        return "今日は、自分のペースを大切に過ごすと良さそうな日です。"

    system_prompt = (
        "あなたは、西洋占星術と天然石の特性に詳しいパーソナルアドバイザーです。\n"
        "生年月日・出生時間・出生地・ホロスコープ情報をもとに、\n"
        "今日のエネルギー傾向を分かりやすく分析してください。\n"
        "神秘的・占い師的な表現は避け、診断レポートのようなトーンで伝えてください。\n"
    ) + SYSTEM_PROMPT

    user_prompt = create_today_fortune_prompt(user_input, chart_data)

    try:
        resp = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=500,
        )

        content = resp.choices[0].message.content.strip()
        content = _strip_code_block(content)
        content = _clean_citations(content)
        return content

    except Exception as e:
        logger.exception("今日の運勢生成でエラー")
        return "今日は、自分のペースを大切に過ごすと良さそうな日です。"


# ===== メイン診断生成 =====

def generate_bracelet_reading(user_input: dict, chart_data: dict = None) -> dict:
    """AIを使ったブレスレット診断を実行する

    オラクルカードをランダムに引き、ユーザー情報と合わせて診断テキストを生成する。
    theme_weights・worry_weights を数値で返し、後続のマッチングに使用する。
    軸となる石はマッチングエンジンが後から決定する。
    """
    client = _get_client()
    if not client:
        return {"error": "鑑定APIの設定が完了していません"}

    # オラクルカードを引く（一般的なテーマカード）
    card = random.choice(ORACLE_CARDS)
    is_upright = random.choice([True, False])
    meaning = card["meaning_up"] if is_upright else card["meaning_rev"]

    oracle_result = {
        "card": card,
        "is_upright": is_upright,
        "meaning": meaning,
    }

    system_msg = (
        "あなたは、西洋占星術と天然石の特性に詳しいパーソナルアドバイザーです。\n"
        "ユーザーの悩みを起点に、ホロスコープで傾向を分析し、診断レポートを作成してください。\n\n"
        "【最重要ルール】\n"
        "ユーザーが自分の言葉で書いた「具体的な悩み」が診断の中心です。\n"
        "ホロスコープや星座はその悩みを読み解くための補足情報として使い、\n"
        "すべてのセクションでユーザーの悩みに具体的に応えてください。\n"
        "神秘的・占い師的な表現は避け、「〜という傾向があります」「〜しやすい状態です」など\n"
        "分かりやすい診断・アドバイスの言葉で伝えてください。\n\n"
        "【前提条件】\n"
        "- ユーザーの「悩み詳細」を最優先で読み取り、具体的に応えること。\n"
        "- 軸となる石はすでに決定済みです。stone_support_message・bracelet_proposal はその石について書くこと。\n"
        "- destiny_map では、出生時間・出生地の情報があれば星座バランスの分析に活かしてください。\n"
    ) + SYSTEM_PROMPT

    user_msg = create_user_prompt(user_input, oracle_result, chart_data)

    try:
        resp = client.chat.completions.create(
            model="sonar-pro",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
            max_tokens=3000,
        )

        content = resp.choices[0].message.content.strip()
        content = _strip_code_block(content)
        content = _clean_citations(content)

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"AIレスポンスのJSONパースに失敗: {content[:200]}")
            result = {}

        if not isinstance(result, dict):
            result = {"destiny_map": str(result)}

        # デフォルト値の設定
        result.setdefault("destiny_map", "")
        result.setdefault("past", "")
        result.setdefault("present_future", "")
        result.setdefault("element_diagnosis", "")
        result.setdefault("oracle_message", "")
        result.setdefault("bracelet_proposal", "")
        result.setdefault("stone_support_message", "")
        result.setdefault("element", "water")
        result.setdefault("theme", choose_theme(user_input.get("concerns", [])))

        # 軸となる石はマッチングエンジンが後から決定する（diagnose.pyで上書き）
        result["stone_name"] = ""

        # theme_weights・worry_weightsをマッチング用に正規化して保持
        result["theme_weights"] = {
            k: float(v) for k, v in (result.get("theme_weights") or {}).items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }
        result["worry_weights"] = {
            k: float(v) for k, v in (result.get("worry_weights") or {}).items()
            if isinstance(v, (int, float)) and not isinstance(v, bool)
        }

        # エレメント情報
        chart_info = build_chart_data(user_input, chart_data)
        result["element_lack"] = chart_info["element_lack"]

        # 画像生成（オラクルカード・星の地図・エレメントバランスの3枚）
        # beads画像はdiagnose.pyがrank1ブレスレットの石で生成する
        from concurrent.futures import ThreadPoolExecutor
        from api.utils_image import (
            generate_oracle_card_image,
            generate_destiny_scene,
            generate_element_balance,
        )

        chart_info_for_img = build_chart_data(user_input, chart_data)
        # 画像生成時の石名はエレメント不足に対応する代表石（石は後から確定）
        stone_for_img = "水晶"

        # キャッシュキーは内容ベース
        position_key = "up" if is_upright else "rev"
        element_key  = f"{chart_info_for_img['element_lack_ja']}-{stone_for_img}"
        balance_key  = f"{chart_info_for_img['fire']}-{chart_info_for_img['earth']}-{chart_info_for_img['wind']}-{chart_info_for_img['water']}"

        # 3枚の画像を並列生成
        with ThreadPoolExecutor(max_workers=3) as executor:
            f_oracle = executor.submit(
                generate_oracle_card_image,
                card["name"], card["en"], is_upright,
                f"oracle-{card['name']}-{position_key}",
            )
            f_destiny = executor.submit(
                generate_destiny_scene,
                chart_info_for_img["element_lack_ja"],
                stone_for_img,
                f"destiny-{element_key}",
                result.get("destiny_map", ""),
            )
            f_element = executor.submit(
                generate_element_balance,
                chart_info_for_img["fire"],
                chart_info_for_img["earth"],
                chart_info_for_img["wind"],
                chart_info_for_img["water"],
                f"element-{balance_key}",
                result.get("element_diagnosis", ""),
            )
            oracle_image  = f_oracle.result()
            destiny_image = f_destiny.result()
            element_image = f_element.result()

        result["oracle_card"] = {
            "name": card["name"],
            "meaning": meaning,
            "is_upright": is_upright,
            "image_url": oracle_image,
        }

        result["images"] = {
            "destiny_scene":   destiny_image,
            "element_balance": element_image,
            "beads":           None,  # diagnose.pyがrank1石で生成
        }

        return result

    except Exception as e:
        logger.exception("Perplexity API エラー")
        return {"error": str(e)}

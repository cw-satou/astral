import os
import json
import re
import random
from openai import OpenAI

# APIキーの取得
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

if PERPLEXITY_API_KEY:
    client = OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai"
    )
else:
    client = None

# 天然石オラクルカードの定義
# name: 日本語名, en: 英語名(プロンプト用), meaning_up: 正位置, meaning_rev: 逆位置
CRYSTAL_ORACLE_CARDS = [
    {
        "name": "アメジスト", "en": "Amethyst crystal", 
        "meaning_up": "精神の安定・直感の覚醒", "meaning_rev": "不安・逃避・考えすぎ"
    },
    {
        "name": "ローズクォーツ", "en": "Rose Quartz crystal",
        "meaning_up": "無条件の愛・自己受容", "meaning_rev": "自信喪失・愛への渇望"
    },
    {
        "name": "シトリン", "en": "Citrine crystal",
        "meaning_up": "繁栄・自信・成功", "meaning_rev": "散財・エネルギー不足"
    },
    {
        "name": "クリアクォーツ", "en": "Clear Quartz crystal",
        "meaning_up": "浄化・新しいスタート", "meaning_rev": "混乱・方向性の喪失"
    },
    {
        "name": "ブラックトルマリン", "en": "Black Tourmaline crystal",
        "meaning_up": "強力な保護・グラウンディング", "meaning_rev": "恐れ・ネガティブな思考"
    },
    {
        "name": "ラピスラズリ", "en": "Lapis Lazuli crystal",
        "meaning_up": "真実・第三の目", "meaning_rev": "コミュニケーション不足・幻想"
    },
    {
        "name": "カーネリアン", "en": "Carnelian crystal",
        "meaning_up": "行動力・情熱", "meaning_rev": "怒り・無気力"
    },
    {
        "name": "ムーンストーン", "en": "Moonstone crystal",
        "meaning_up": "女性性・神秘・予感", "meaning_rev": "感情の不安定・迷い"
    }
]

SYSTEM_PROMPT = """
あなたは、西洋占星術とクリスタルヒーリングに精通したプロの占い師であり、ジュエリーデザイナーです。
ユーザーの悩みに寄り添い、希望を与え、具体的な解決策としてパワーストーンブレスレットを提案してください。

【出力形式の絶対ルール】
1. **JSON形式**のみを出力すること。Markdownのコードブロックは不要。
2. 引用表記（[1]など）は削除すること。
3. ユーザーの「悩み詳細」を深く読み取り、共感のこもった鑑定を行うこと。

【鑑定文の構成】
以下の構成で、各セクションの間に改行を入れてください。
- **【現状の星回り】**: ホロスコープから読み解く現状
- **【オラクルカードのメッセージ】**: 引いたカードの結果（正位置/逆位置）を踏まえたメッセージ
- **【石からの導き】**: なぜこの石を選んだか、どうサポートしてくれるか
- **【未来へのアドバイス】**: 具体的な行動指針
"""

AVAILABLE_STONES = """
- アメジスト（紫）
- ローズクォーツ（ピンク）
- シトリン（黄）
- 水晶（透明）
- オニキス（黒）
- アクアマリン（水色）
- ラピスラズリ（紺）
- タイガーアイ（茶金）
- ムーンストーン（白）
- カーネリアン（赤）
"""

def create_user_prompt(user_input, oracle_result):
    birth = user_input.get('birth', {})

    # オラクル結果の文字列作成
    position_str = "【正位置】" if oracle_result['is_upright'] else "【逆位置】"
    oracle_text = f"カード: {oracle_result['card']['name']}\n状態: {position_str}\n意味: {oracle_result['meaning']}"

    return f"""
以下のユーザー情報と、先ほど引いた「天然石オラクルカード」の結果に基づき、鑑定を行ってください。

【オラクルカード結果】
{oracle_text}

【ユーザー情報】
- 性別: {user_input.get('gender', '指定なし')}
- 悩み: {user_input.get('problem', '指定なし')}
- 生年月日: {birth.get('date', '不明')}

【使用可能な石リスト】
{AVAILABLE_STONES}

【出力JSONスキーマ】
{{
  "reading": "（600文字程度の鑑定結果。オラクルカードの結果（正位置/逆位置）にも必ず触れること）",
  "stones": [
    {{
      "name": "（石の名前）",
      "reason": "（その石を選んだ理由）",
      "count": （個数・整数）,
      "position": "（top / side / base / accent）"
    }}
  ],
  "design_concept": "（ブレスレットのデザインテーマ）",
  "design_text": "（デザインの解説）",
  "sales_copy": "（商品紹介文）"
}}
"""

def generate_bracelet_reading(user_input: dict) -> dict:
    if not client:
        return {"error": "Perplexity API Key not configured"}

    # 1. オラクルカード抽選（石を選ぶ + 正逆を決める）
    card = random.choice(CRYSTAL_ORACLE_CARDS)
    is_upright = random.choice([True, False]) # 50%で正位置/逆位置

    meaning = card['meaning_up'] if is_upright else card['meaning_rev']

    oracle_result = {
        "card": card,
        "is_upright": is_upright,
        "meaning": meaning
    }

    # 2. AI鑑定実行
    system_msg = SYSTEM_PROMPT
    user_msg = create_user_prompt(user_input, oracle_result)

    try:
        resp = client.chat.completions.create(
            model="sonar-pro", 
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
        )

        content = resp.choices[0].message.content

        # クリーニング
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
             content = content.split("```")[1].split("```")[0].strip()
        content = re.sub(r'\[\d+\]', '', content)

        result = json.loads(content)

        # 3. 画像生成URL (Pollinations.ai)
        # オラクルカード画像（常に正位置の美しさを描画）
        card_prompt = f"oracle card art of {card['en']}, mystical glowing gemstone, divine light, intricate golden border, fantasy art, tarot style, high quality, 8k"
        card_image_url = f"https://image.pollinations.ai/prompt/{card_prompt.replace(' ', '%20')}?width=400&height=600&seed={random.randint(0,9999)}"

        # ブレスレット画像
        stone_names_en = ", ".join([s['name'] for s in result.get('stones', [])])
        bracelet_prompt = f"gemstone bracelet, {stone_names_en}, jewelry photography, soft lighting, white background, high quality, 8k"
        bracelet_image_url = f"https://image.pollinations.ai/prompt/{bracelet_prompt.replace(' ', '%20')}?width=600&height=400&seed={random.randint(0,9999)}"

        # 結果に統合
        result['oracle_card'] = {
            'name': card['name'],
            'meaning': meaning,
            'is_upright': is_upright, # HTML側でこれを見て画像を回転させる
            'image_url': card_image_url
        }
        result['bracelet_image_url'] = bracelet_image_url

        return result

    except Exception as e:
        print(f"Perplexity API Error: {e}")
        return {"error": str(e)}

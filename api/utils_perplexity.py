import os
import json
import re
from openai import OpenAI

# APIキーの取得
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# クライアント初期化
if PERPLEXITY_API_KEY:
    client = OpenAI(
        api_key=PERPLEXITY_API_KEY,
        base_url="https://api.perplexity.ai"
    )
else:
    client = None

SYSTEM_PROMPT = """
あなたは、西洋占星術とクリスタルヒーリングに精通したプロの占い師であり、ジュエリーデザイナーです。
ユーザーの悩みに寄り添い、希望を与え、具体的な解決策としてパワーストーンブレスレットを提案してください。

【出力形式の絶対ルール】
1. **JSON形式**のみを出力すること。Markdownのコードブロック（```json）は不要です。
2. **引用表記（[1], [2]など）は絶対に含まないこと。**
3. 文章は適度に改行し、読みやすくすること。

【鑑定文（reading）の構成ルール】
以下の構成で、各セクションの間に改行を入れてください。
- **【現状の星回り】**: ホロスコープから読み解く現状
- **【原因と課題】**: 悩みの根本原因
- **【未来へのアドバイス】**: 今後の指針と解決策
"""

AVAILABLE_STONES = """
- アメジスト（紫、6mm/8mm/10mm）: 精神安定、直感
- ローズクォーツ（ピンク、6mm/8mm/10mm）: 恋愛、自己肯定
- シトリン（黄、6mm/8mm）: 金運、繁栄
- 水晶（透明、6mm/8mm/10mm/12mm）: 浄化、調和
- オニキス（黒、8mm/10mm）: 魔除け、忍耐
- アクアマリン（水色、6mm/8mm）: 癒し、コミュニケーション
- ラピスラズリ（紺、8mm/10mm）: 真実、幸運
- タイガーアイ（茶金、8mm/10mm）: 仕事運、洞察力
- ムーンストーン（白、6mm/8mm）: 女性性、感受性
- カーネリアン（赤、6mm/8mm）: 活力、勇気
"""

def create_user_prompt(user_input):
    # 安全にデータを取り出す（KeyError防止）
    birth = user_input.get('birth', {})

    return f"""
以下のユーザー情報に基づき、ホロスコープを読み解き、最適なパワーストーンブレスレットを設計してください。

【ユーザー情報】
- 性別: {user_input.get('gender', '指定なし')}
- 悩み: {user_input.get('problem', '指定なし')}
- デザインの希望: {user_input.get('design_pref', '指定なし')}
- 生年月日: {birth.get('date', '不明')}
- 出生時間: {birth.get('time', '不明')}
- 出生地: {birth.get('place', '不明')}

【使用可能な石リスト】
{AVAILABLE_STONES}

【出力JSONスキーマ】
{{
  "reading": "（400文字以内の鑑定結果。必ず【小見出し】を使い、段落ごとに改行を入れて読みやすくすること。引用表記[1]などは削除すること）",
  "stones": [
    {{
      "name": "（石の名前）",
      "reason": "（その石を選んだ理由）",
      "count": （個数・整数）,
      "position": "（top / side / base / accent のいずれか）"
    }}
  ],
  "design_concept": "（ブレスレットのデザインテーマ）",
  "design_text": "（デザインの解説。150文字以内）",
  "sales_copy": "（商品としての魅力的な紹介文。200文字以内）"
}}
"""

def generate_bracelet_reading(user_input: dict) -> dict:
    if not client:
        return {"error": "Perplexity API Key not configured"}

    system_msg = SYSTEM_PROMPT
    user_msg = create_user_prompt(user_input)

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

        # 1. Markdownのコードブロック削除
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
             content = content.split("```")[1].split("```")[0].strip()

        # 2. 引用表記（[1], [10]など）を正規表現で強制削除
        content = re.sub(r'\[\d+\]', '', content)

        # 3. JSONロード
        return json.loads(content)

    except Exception as e:
        print(f"Perplexity API Error: {e}")
        return {"error": str(e)}

# api/utils_perplexity.py
import os
import json
from openai import OpenAI 

# APIキーの取得
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY")

# クライアント初期化（Perplexityのサーバーを指定）
client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

SYSTEM_PROMPT = """
あなたは、西洋占星術とクリスタルヒーリングに精通したプロの占い師であり、
ジュエリーデザイナーでもあります。
ユーザーの悩みに寄り添い、希望を与え、具体的な解決策としてパワーストーンブレスレットを提案してください。

【重要な制約事項】
1. 出力は必ずJSON形式のみを行ってください。余計な挨拶やMarkdown装飾は不要です。
2. JSONの構造は指定されたスキーマを厳守してください。
3. 石の選定は、以下の「使用可能な石リスト」の中から選んでください。リストにない石は使わないでください。
4. 鑑定結果の文章は、ユーザーに語りかけるような、優しく神秘的な口調（です・ます調）で書いてください。
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
    return f"""
以下のユーザー情報に基づき、ホロスコープを読み解き、最適なパワーストーンブレスレットを設計してください。

【ユーザー情報】
- 悩み: {user_input.get('problem')}
- デザインの希望: {user_input.get('design_pref')}
- 生年月日: {user_input['birth'].get('date')}
- 出生時間: {user_input['birth'].get('time')}
- 出生地: {user_input['birth'].get('place')}

【使用可能な石リスト】
{AVAILABLE_STONES}

【出力JSONフォーマット】
{{
  "reading": "（400文字以内の鑑定結果。星の配置（太陽星座、月星座など）に触れながら、なぜ今の悩みが生じているのか、どうすれば解決に向かうかを優しく説く文章）",
  "stones": [
    {{
      "name": "（石の名前）",
      "reason": "（その石を選んだ理由。占星術的な根拠や石の効果）",
      "count": （個数・整数）,
      "position": "（top / side / base / accent のいずれか）"
    }}
  ],
  "design_concept": "（ブレスレットのデザインテーマ。例：「夜明けの空」「桜舞う小道」など、情景が浮かぶようなタイトル）",
  "design_text": "（デザインの解説。色の組み合わせや配置の意図など、150文字以内）",
  "sales_copy": "（商品としての魅力的な紹介文。200文字以内）"
}}
"""

def generate_bracelet_reading(user_input: dict) -> dict:
    if not PERPLEXITY_API_KEY:
        return {"error": "Perplexity API Key not configured"}

    system_msg = SYSTEM_PROMPT
    user_msg = create_user_prompt(user_input)

    try:
        # 変更点: client.chat.completions.create を使う
        resp = client.chat.completions.create(
            model="sonar-pro",  # または "sonar"
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.7,
        )
        
        content = resp.choices[0].message.content
        
        # JSON部分だけを取り出す処理
        if "```json" in content:
            content = content.split("```json").split("```").strip()[1]
        elif "```" in content:
             content = content.split("```")[16].split("```")[0].strip()
        
        return json.loads(content)
        
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}
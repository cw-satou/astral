import os
import requests
from flask import request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage, FlexMessage
)
from linebot.v3.webhooks import (
    MessageEvent, TextMessageContent
)

CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


# ==========================
# Webhookエントリ
# ==========================
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ==========================
# メッセージ受信処理
# ==========================
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        if len(user_text) >= 8:
            try:
                response = requests.post(
                    os.environ.get("API_BASE_URL") + "/api/fortune-detail",
                    json={"diagnosis_id": user_text}
                )

                if response.status_code == 200:
                    data = response.json()

                    reply_text = f"""
【あなたの運命の地図】

■ 過去
{data.get('past')}

■ 現在
{data.get('present')}

■ 未来
{data.get('future')}

━━━━━━━━━━

あなたの背中を押して、ずっと寄り添う石は
『{data.get('stone_name')}』です。
"""

                    flex_content = build_product_flex(
                        data.get("stone_name"),
                        data.get("product_urls")
                    )

                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            replyToken=event.reply_token,
                            messages=[
                                TextMessage(text=reply_text),
                                FlexMessage(
                                    altText="あなたの羅針盤はこちらです",
                                    contents=flex_content
                                )
                            ]
                        )
                    )
                    return

                else:
                    reply_text = "診断IDが見つかりませんでした。"

            except Exception:
                reply_text = "詳細取得中にエラーが発生しました。"

        else:
            reply_text = """星の羅針盤へようこそ✨

無料診断はこちら：
https://your-liff-url.com
"""

        line_bot_api.reply_message(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

def build_product_flex(stone_name, product_urls):

    def bubble(title, subtitle, url):
        return {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": title,
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": subtitle,
                        "size": "sm",
                        "color": "#888888",
                        "wrap": True
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "この羅針盤を迎える",
                            "uri": url
                        }
                    }
                ]
            }
        }

    return {
        "type": "carousel",
        "contents": [
            bubble(
                f"{stone_name}（トップ）",
                "最もエネルギーが集中する設計",
                product_urls["top"]
            ),
            bubble(
                f"{stone_name}（単色）",
                "石の力をまっすぐ受け取る",
                product_urls["single"]
            ),
            bubble(
                f"{stone_name}（2色）",
                "調和とバランスを整える設計",
                product_urls["double"]
            )
        ]
    }
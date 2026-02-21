import os
import requests
from flask import request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi,
    ReplyMessageRequest, TextMessage
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

    # 診断IDっぽい文字列なら詳細取得
    if len(user_text) >= 8:

        try:
            # 自分のAPIに問い合わせ
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

■ エレメント診断
{data.get('element_detail')}

■ オラクルカード
{data.get('oracle_name')}（{data.get('oracle_position')}）

━━━━━━━━━━

あなたの背中を押して、ずっと寄り添う石は
『{data.get('stone_name')}』です。

▶ ブレスレットを見る
{data.get('product_url')}
"""

            else:
                reply_text = "診断IDが見つかりませんでした。もう一度ご確認ください。"

        except Exception as e:
            reply_text = "詳細取得中にエラーが発生しました。"

    else:
        reply_text = """星の羅針盤へようこそ✨

無料診断はこちらから行えます：
https://your-liff-url.com

診断後に表示される「診断ID」を
このトークに送ってください。
詳細鑑定をお届けします。"""

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                replyToken=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
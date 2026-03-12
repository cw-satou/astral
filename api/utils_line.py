import requests
import os

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

def push_line(user_id, message):

    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

    if not token:
        print("LINE token not set")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    requests.post(LINE_PUSH_URL, json=body, headers=headers)
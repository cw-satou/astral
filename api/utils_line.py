import requests
import os

LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"

def push_line(user_id, message):

    headers = {
        "Authorization": f"Bearer {os.environ['LINE_CHANNEL_ACCESS_TOKEN']}",
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
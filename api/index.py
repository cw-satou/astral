# api/index.py
from flask import Flask, request, jsonify, abort
from api.diagnose import diagnose  # 診断処理をインポート
from api.line_webhook import callback # Webhook処理をインポート

app = Flask(__name__)

# ルーティングをここでまとめて定義する
# （元々のファイルから @app.route を剥がしてここに集約するイメージですが、
#  一番簡単なのは、元の関数をそのまま route に登録することです）

app.add_url_rule('/api/diagnose', view_func=diagnose, methods=['POST'])
app.add_url_rule('/api/line_webhook', view_func=callback, methods=['POST'])

# 動作確認用（ブラウザで /api/test にアクセスすると動いているかわかる）
@app.route('/api/test')
def test():
    return "API is working!"

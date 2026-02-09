from flask import Flask, request, jsonify
import os

# ルーティングのインポート
from api.diagnose import diagnose, build_bracelet

app = Flask(__name__, static_folder='public', static_url_path='')

# ===== ルーティング =====

@app.route('/api/diagnose', methods=['POST'])
def route_diagnose():
    """占い処理エンドポイント"""
    return diagnose()

@app.route('/api/build-bracelet', methods=['POST'])
def route_build_bracelet():
    """ブレスレット生成エンドポイント"""
    return build_bracelet()

@app.route('/api/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return jsonify({"status": "ok", "service": "星の羅針盤 API"})

@app.route('/')
def index():
    """フロントエンド提供"""
    return app.send_static_file('index.html')

# ===== エラーハンドラー =====

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # ローカル開発用
    app.run(debug=True, port=5000)
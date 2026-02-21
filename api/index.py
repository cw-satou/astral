from flask import Flask, request, jsonify
import os

# ルーティングのインポート
from api.diagnose import diagnose, build_bracelet
from api.utils_sheet import get_diagnosis

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

@app.route('/api/fortune-detail', methods=['POST'])
def fortune_detail():
    data = request.get_json(force=True, silent=True) or {}
    diagnosis_id = data.get("diagnosis_id")

    if not diagnosis_id:
        return jsonify({"error": "diagnosis_id is required"}), 400

    saved = get_diagnosis(diagnosis_id)

    if not saved:
        return jsonify({"error": "Diagnosis not found"}), 404

    base_url = os.environ.get("SHOP_BASE_URL", "https://yourshop.com/product/")
    if base_url == "":
        base_url = "https://yourshop.com/product/";

    # 🔥 ここが3商品化ポイント
    product_slug_top = saved.get("product_slug") or "top-crystal"

    if not product_slug_top.startswith("top-"):
        product_slug_top = "top-" + product_slug_top

    product_slug_single = product_slug_top.replace("top-", "single-")
    product_slug_double = product_slug_top.replace("top-", "double-")

    product_urls = {
        "top": base_url + product_slug_top,
        "single": base_url + product_slug_single,
        "double": base_url + product_slug_double
    }

    response = {
        "diagnosis_id": saved.get("diagnosis_id"),
        "stone_name": saved.get("stone_name"),
        "past": saved.get("past"),
        "present": saved.get("present"),
        "future": saved.get("future"),
        "element_detail": saved.get("element_detail"),
        "oracle_name": saved.get("oracle_name"),
        "oracle_position": saved.get("oracle_position"),
        "product_urls": product_urls
    }

    return jsonify(response)

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
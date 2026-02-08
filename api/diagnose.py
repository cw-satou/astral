from flask import Flask, request, jsonify
from api.utils_perplexity import generate_bracelet_reading
from api.utils_order import build_order_summary
import json

def diagnose():
    try:
        # 1. リクエストボディの安全な取得
        data = request.get_json(force=True, silent=True)

        if not data:
            # get_json失敗時のバックアップ処理
            try:
                if request.data:
                    data = json.loads(request.data)
                else:
                    return jsonify({"error": "Empty request body"}), 400
            except Exception as e:
                return jsonify({"error": "Invalid JSON format", "detail": str(e)}), 400

        # デバッグ用：受け取ったデータを確認したい場合はコメントアウトを外す
        print(f"Received data: {data}")

        # 2. AIによる分析実行
        result = generate_bracelet_reading(data)

        # AI側でエラーが起きた場合
        if "error" in result:
             return jsonify(result), 500

        # 3. オーダー情報の生成（安全に値を取得）
        try:
            wrist_inner_cm = float(data.get("wrist_inner_cm") or 15.0)
            bead_size_mm = int(data.get("bead_size_mm") or 8)
        except ValueError:
            # 数値変換に失敗した場合はデフォルト値を使う
            wrist_inner_cm = 15.0
            bead_size_mm = 8

        order_summary = build_order_summary(result, wrist_inner_cm, bead_size_mm)

        # 4. (TODO) Save to Google Sheets or Database here
        # save_to_db(data, result, order_summary)

        diagnosis_id = "diag_sample_12345"

        return jsonify({
            "diagnosis_id": diagnosis_id,
            "result": result,
            "order_summary": order_summary
        })

    except Exception as e:
        # 予期せぬエラーの捕捉
        print(f"Critical Server Error: {str(e)}")
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500
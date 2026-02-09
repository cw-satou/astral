from flask import request, jsonify
import uuid
import json
import traceback
import sys
import time

# 内部モジュールのインポート
from api.utils_perplexity import generate_bracelet_reading
from api.utils_order import build_order_summary
from api.utils_sheet import save_to_sheet
from api.utils_mail import send_order_mail

def diagnose():
    """
    メイン占い処理エンドポイント

    リクエスト形式:
    {
        "gender": "女性|男性|その他",
        "concerns": ["恋愛", "仕事"],  # 複数選択可
        "problem": "具体的な悩みテキスト",
        "birth": {
            "date": "1990-05-15",
            "time": "14:30",
            "place": "札幌市"
        },
        "wrist_inner_cm": 15.0,
        "bead_size_mm": 8
    }
    """
    start_time = time.time()
    print("--- Diagnose Request Started ---")

    try:
        # 1. リクエストボディの取得
        data = request.get_json(force=True, silent=True)

        if not data:
            try:
                if request.data:
                    data = json.loads(request.data.decode('utf-8'))
                else:
                    print("Error: Empty request body")
                    return jsonify({"error": "Empty request body", "code": "EMPTY_BODY"}), 400
            except Exception as e:
                print(f"Error parsing raw data: {str(e)}")
                return jsonify({"error": "Invalid JSON format", "detail": str(e), "code": "JSON_PARSE_ERROR"}), 400

        print(f"Received data (concerns: {data.get('concerns', [])})")

        # ---------------------------------------------------------
        # 2. AIによる分析実行 (Perplexity API)
        # ---------------------------------------------------------
        print("Calling Perplexity API for bracelet reading...")

        try:
            result = generate_bracelet_reading(data)
        except Exception as ai_err:
            print(f"AI Generation Error: {str(ai_err)}")
            traceback.print_exc()
            return jsonify({
                "error": "AI Processing Error",
                "message": str(ai_err),
                "code": "AI_ERROR"
            }), 500

        # AI側の戻り値に明示的なエラーが含まれている場合
        if isinstance(result, dict) and "error" in result:
            print(f"AI Returned Error: {result}")
            return jsonify(result), 500

        print("AI Response Received.")

        # ---------------------------------------------------------
        # 3. オーダー情報の生成
        # ---------------------------------------------------------
        try:
            # 安全な型変換
            wrist_inner_cm = float(data.get("wrist_inner_cm") or 15.0)
            bead_size_mm = int(data.get("bead_size_mm") or 8)
        except ValueError as ve:
            print(f"Value Error in dimensions: {ve}")
            wrist_inner_cm = 15.0
            bead_size_mm = 8

        order_summary = build_order_summary(result, wrist_inner_cm, bead_size_mm)
        diagnosis_id = str(uuid.uuid4())[:8]

        print(f"Order summary created: {diagnosis_id}")

        # ---------------------------------------------------------
        # 4. Google Sheets への保存
        # ---------------------------------------------------------
        try:
            print("Saving to Google Sheets...")
            save_to_sheet(data, result, diagnosis_id)
            print("Saved to Sheet successfully.")
        except Exception as sheet_err:
            # シート保存エラーはログに出すが、処理は止めない
            print(f"⚠️  Warning: Failed to save to sheet: {str(sheet_err)}")

        # ---------------------------------------------------------
        # 5. メール送信（オーダー確定時）
        # ---------------------------------------------------------
        try:
            print("Sending order mail...")
            send_order_mail(order_summary, diagnosis_id)
        except Exception as mail_err:
            # メール送信エラーもログに出すが、処理は止めない
            print(f"⚠️  Warning: Failed to send mail: {str(mail_err)}")

        # 処理時間の計測ログ
        elapsed_time = time.time() - start_time
        print(f"✅ Diagnose finished in {elapsed_time:.2f} seconds.")

        # ---------------------------------------------------------
        # 6. 成功レスポンス
        # ---------------------------------------------------------
        response_data = {
            "diagnosis_id": diagnosis_id,
            "result": result,  # ここに運命の地図・過去/現在/未来・エレメント診断・オラクルメッセージなどが入っている
            "order_summary": order_summary
        }

        return jsonify(response_data)

    except Exception as e:
        # 予期せぬエラーの捕捉
        t, v, tb = sys.exc_info()
        print(f"❌ Critical Server Error: {str(e)}")
        traceback.print_exc()

        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": "CRITICAL_ERROR"
        }), 500


def confirm_order():
    """
    オーダー確認エンドポイント（オプション）
    ユーザーが「このブレスレットでいいですか？」という画面からの確認処理
    """
    try:
        data = request.get_json(force=True, silent=True)

        diagnosis_id = data.get("diagnosis_id")
        # 確認済みフラグ etc. の処理

        print(f"Order confirmed: {diagnosis_id}")

        # ここでメール送信やシート更新等を行うことも可能
        return jsonify({"status": "confirmed", "diagnosis_id": diagnosis_id})

    except Exception as e:
        print(f"Error in confirm_order: {str(e)}")
        return jsonify({"error": str(e)}), 500

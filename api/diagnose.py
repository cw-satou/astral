from flask import request, jsonify
# 内部モジュールのインポート（パス構成によっては .utils... になる場合もあります）
from api.utils_perplexity import generate_bracelet_reading
from api.utils_order import build_order_summary
from api.utils_sheet import save_to_sheet
import uuid
import json
import traceback
import sys

# Vercelのタイムアウト(Hobby:10s, Pro:60s)を考慮し
# 処理時間を計測するためのモジュール
import time

def diagnose():
    start_time = time.time()
    print("--- Diagnose Request Started ---")

    try:
        # 1. リクエストボディの取得
        # force=True: Content-TypeヘッダがなくてもJSONとして解析
        # silent=True: 解析失敗時にエラーを吐かず None を返す
        data = request.get_json(force=True, silent=True)

        if not data:
            # get_json失敗時のバックアップ処理（生のデータをパース試行）
            try:
                if request.data:
                    data = json.loads(request.data.decode('utf-8'))
                else:
                    print("Error: Empty request body")
                    return jsonify({"error": "Empty request body", "code": "EMPTY_BODY"}), 400
            except Exception as e:
                print(f"Error parsing raw data: {str(e)}")
                return jsonify({"error": "Invalid JSON format", "detail": str(e), "code": "JSON_PARSE_ERROR"}), 400

        # デバッグログ: 入力データの内容確認（個人情報に注意）
        # dataの中身が大きすぎる場合は一部だけ出すなどの配慮も可
        print(f"Received data: {data}")

        # ---------------------------------------------------------
        # 2. AIによる分析実行 (Perplexity API)
        # ---------------------------------------------------------
        print("Calling Perplexity API...")
        
        # utils_perplexity側でもエラーハンドリングされている前提ですが、
        # ここでも例外をキャッチできるようにしておく
        try:
            result = generate_bracelet_reading(data)
        except Exception as ai_err:
            print(f"AI Generation Error: {str(ai_err)}")
            # トレースバックを出力してログに残す
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

        # ---------------------------------------------------------
        # 4. Google Sheets への保存
        # ---------------------------------------------------------
        # シート保存は失敗しても、ユーザーへの結果表示（占い結果）は返したい場合が多い
        # なので、try-catch をここだけ独立させても良い
        try:
            print("Saving to Google Sheets...")
            save_to_sheet(data, result, diagnosis_id)
            print("Saved to Sheet.")
        except Exception as sheet_err:
            # シート保存エラーはログに出すが、処理は止めない（クリティカルではないとする場合）
            print(f"Warning: Failed to save to sheet: {str(sheet_err)}")
            # traceback.print_exc()
            # 必要ならここで return 500 しても良い

        # 処理時間の計測ログ
        elapsed_time = time.time() - start_time
        print(f"Diagnose finished in {elapsed_time:.2f} seconds.")

        # 5. 成功レスポンス
        response_data = {
            "diagnosis_id": diagnosis_id,
            "result": result,          # ここに占いテキストが入っている想定
            "order_summary": order_summary
        }
        return jsonify(response_data)

    except Exception as e:
        # 予期せぬエラーの捕捉
        # スタックトレースをログに出すことで、どこで落ちたか特定しやすくする
        t, v, tb = sys.exc_info()
        print(f"Critical Server Error: {str(e)}")
        traceback.print_exc() 

        # ユーザー（LIFF）に返すエラー情報
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": "CRITICAL_ERROR"
        }), 500

from flask import request, jsonify
from api.utils_perplexity import generate_bracelet_reading
from api.utils_order import build_order_summary
from api.utils_sheet import save_to_sheet
import uuid
import json
import traceback
import sys
import time

def diagnose():
    """
    第1フェーズ：占い結果だけを返す（サイズは聞かない）
    """
    start_time = time.time()
    print("--- Diagnose Request Started (Phase 1: Divination Only) ---")
    
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
        
        print(f"Received data: {data}")
        
        # 2. AIによる分析実行
        print("Calling Perplexity API for divination...")
        
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
        
        # AIがエラーを返した場合
        if isinstance(result, dict) and "error" in result:
            print(f"AI Returned Error: {result}")
            return jsonify(result), 500
        
        print("AI Response Received.")
        
        # 3. 診断IDの生成
        diagnosis_id = str(uuid.uuid4())[:8]
        
        # 4. この段階ではGoogle Sheetsに保存（ユーザー基本情報のみ）
        try:
            print("Saving to Google Sheets...")
            save_to_sheet(data, result, diagnosis_id)
            print("Saved to Sheet.")
        except Exception as sheet_err:
            print(f"Warning: Failed to save to sheet: {str(sheet_err)}")
        
        # 処理時間の計測ログ
        elapsed_time = time.time() - start_time
        print(f"Diagnose finished in {elapsed_time:.2f} seconds.")
        
        # 5. 成功レスポンス（占い結果＋石候補のみ）
        response_data = {
            "diagnosis_id": diagnosis_id,
            "phase": "stones_only",  # フロント用フラグ
            "result": result,
            "input_data": data  # サイズ決定フェーズで必要
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        t, v, tb = sys.exc_info()
        print(f"Critical Server Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e),
            "code": "CRITICAL_ERROR"
        }), 500


def build_bracelet():
    """
    第2フェーズ：石候補 + 手首サイズ + ビーズサイズから、完成ブレスレットを生成
    """
    start_time = time.time()
    print("--- Build Bracelet Request Started (Phase 2: Size & Design) ---")
    
    try:
        # 1. リクエストボディの取得
        data = request.get_json(force=True, silent=True) or {}
        
        print(f"Received bracelet data: {data}")
        
        # 2. パラメータ取得
        diagnosis_id = data.get("diagnosis_id", str(uuid.uuid4())[:8])
        stones_for_user = data.get("stones_for_user", [])
        
        try:
            wrist_inner_cm = float(data.get("wrist_inner_cm") or 15.0)
            bead_size_mm = int(data.get("bead_size_mm") or 8)
        except ValueError as ve:
            print(f"Value Error in dimensions: {ve}")
            wrist_inner_cm = 15.0
            bead_size_mm = 8
        
        # 3. ブレスレットデザイン生成
        bracelet_design = build_bracelet_design(stones_for_user, wrist_inner_cm, bead_size_mm)
        stones = bracelet_design["stones"]
        design_text = bracelet_design["design_text"]
        
        # 4. オーダー情報の生成
        mock_result = {
            "reading": "（占い結果は第1フェーズから）",
            "stones": stones,
            "design_concept": bracelet_design.get("design_concept", ""),
            "design_text": design_text,
            "sales_copy": bracelet_design.get("sales_copy", "")
        }
        
        order_summary = build_order_summary(mock_result, wrist_inner_cm, bead_size_mm)
        
        # 処理時間の計測ログ
        elapsed_time = time.time() - start_time
        print(f"Build bracelet finished in {elapsed_time:.2f} seconds.")
        
        # 5. 成功レスポンス
        response_data = {
            "diagnosis_id": diagnosis_id,
            "phase": "bracelet_complete",
            "design_text": design_text,
            "stones": stones,
            "order_summary": order_summary,
            "wrist_inner_cm": wrist_inner_cm,
            "bead_size_mm": bead_size_mm
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Bracelet Build Error: {str(e)}")
        traceback.print_exc()
        return jsonify({
            "error": "Bracelet Build Error",
            "message": str(e),
            "code": "BRACELET_ERROR"
        }), 500


def build_bracelet_design(stones_for_user: list, wrist_inner_cm: float, bead_size_mm: int) -> dict:
    """
    石候補 + サイズから、ブレスレットの個数・配置を決める
    """
    if not stones_for_user:
        return {
            "stones": [],
            "design_concept": "未指定",
            "design_text": "石の候補が取得できませんでした。"
        }
    
    # 必要な粒数をざっくり計算（ゴムの余裕を含む）
    bracelet_length_mm = wrist_inner_cm * 10 + 10
    total_bead_count = max(12, int(bracelet_length_mm / bead_size_mm))
    
    # メイン・サブを分ける
    main = stones_for_user[0]
    subs = stones_for_user[1:] if len(stones_for_user) > 1 else stones_for_user
    
    # 個数と配置を決める
    stones = []
    
    # メイン石を中心（top）に配置
    main_count = max(1, int(total_bead_count * 0.4))
    for i in range(main_count):
        stones.append({
            "name": main["name"],
            "reason": main["reason"],
            "count": 1,
            "position": "top"
        })
    
    # サブ石をバランスよく配置
    remaining = total_bead_count - main_count
    if subs:
        per_sub = max(1, remaining // len(subs))
        for sub in subs:
            sub_count = min(per_sub, remaining)
            if sub_count > 0:
                stones.append({
                    "name": sub["name"],
                    "reason": sub["reason"],
                    "count": sub_count,
                    "position": "side"
                })
                remaining -= sub_count
    
    # 余った粒をメインに足す
    if remaining > 0:
        stones[0]["count"] = stones[0].get("count", 1) + remaining
    
    design_concept = f"「{main['name']}」を中心としたメディテーションブレス"
    design_text = (
        f"メインストーンには「{main['name']}」を中心に据え、"
        f"サポートストーンをバランスよく組み合わせたデザインです。"
        f"あなたの願いを日常的に後押しするお守りブレスレットとして仕上げます。"
    )
    
    return {
        "stones": stones,
        "design_concept": design_concept,
        "design_text": design_text,
        "sales_copy": f"あなたを導く {main['name']} ブレスレット"
    }

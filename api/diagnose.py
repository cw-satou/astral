from flask import Flask, request, jsonify
from api.utils_perplexity import generate_bracelet_reading
from api.utils_order import build_order_summary

# Note: In Vercel, this file usually exports 'app' which is handled by WSGI.
# The route decorator path should match your Vercel rewrites or file structure.

def diagnose():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # data structure expected:
        # {
        #   "problem": "...",
        #   "design_pref": "...",
        #   "birth": {"date": "...", "time": "...", "place": "..."},
        #   "wrist_inner_cm": 15.0, (optional)
        #   "bead_size_mm": 8 (optional)
        # }

        # 1. AI Analysis
        result = generate_bracelet_reading(data)

        if "error" in result:
             return jsonify(result), 500

        # 2. Build Order Info
        wrist_inner_cm = float(data.get("wrist_inner_cm") or 15.0)
        bead_size_mm = int(data.get("bead_size_mm") or 8)

        order_summary = build_order_summary(result, wrist_inner_cm, bead_size_mm)

        # 3. (TODO) Save to Google Sheets or Database here
        # save_to_db(data, result, order_summary)

        # Generate a dummy diagnosis ID
        diagnosis_id = "diag_sample_12345"

        return jsonify({
            "diagnosis_id": diagnosis_id,
            "result": result,
            "order_summary": order_summary
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

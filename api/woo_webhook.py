from flask import request, jsonify
from api.utils_sheet import add_order
from api.utils_line import push_line
from api.utils_sheet import get_diagnosis

def woo_webhook():

    order = request.json

    order_id = order["id"]

    diagnosis_id = None

    for item in order["line_items"]:
        for meta in item.get("meta_data", []):
            if meta.get("key") == "diagnosis_id":
                diagnosis_id = meta.get("value")

    data = {
        "order_id":order_id,
        "diagnosis_id":diagnosis_id,
        "created_at":order["date_created"]
    }

    add_order(data)

    diagnosis = get_diagnosis(diagnosis_id)
    if not diagnosis:
        print("diagnosis not found")
        return jsonify({"status": "diagnosis not found"})

    user_id = diagnosis.get("user_line_id")

    diagnosis_id = None
    for item in order.get("line_items", []):
        for meta in item.get("meta_data", []):
            if meta.get("key") == "diagnosis_id":
                diagnosis_id = meta.get("value")
                break

    if not diagnosis_id:
        print("diagnosis_id not found")
        return jsonify({"status":"no diagnosis id"})

    message = f"""
    ご注文ありがとうございます✨

    ■使用する石
    {diagnosis['stones']}

    制作を開始します。
    """
    if not user_id:
        return jsonify({"status":"no user id"})
    push_line(user_id,message)

    return jsonify({"status":"ok"})
"""WooCommerce Webhook処理モジュール

WooCommerceから注文通知を受け取り、以下を実行する:
1. 注文情報をGoogleスプレッドシートに記録
2. 診断結果に紐づくLINEユーザーに注文確認メッセージを送信
   ※LINE未登録ユーザーの場合はスキップ（購入機会の損失防止）
3. 管理者へメール通知
"""

import logging
from flask import request, jsonify
from api.utils_sheet import add_order, get_diagnosis, mark_purchased
from api.utils_line import push_line
from api.utils_mail import send_order_mail

logger = logging.getLogger(__name__)


def _extract_diagnosis_id(order: dict) -> str | None:
    """注文のline_itemsからdiagnosis_idメタデータを抽出する"""
    for item in order.get("line_items", []):
        for meta in item.get("meta_data", []):
            if meta.get("key") == "diagnosis_id":
                return meta.get("value")
    return None


def _build_order_summary_for_mail(order: dict, diagnosis_id: str | None) -> dict:
    """メール通知用の注文サマリーを構築する"""
    billing = order.get("billing", {})
    items = []
    for item in order.get("line_items", []):
        items.append({
            "name": item.get("name", ""),
            "quantity": item.get("quantity", 0),
            "total": item.get("total", "0"),
        })

    return {
        "order_id": order.get("id"),
        "status": order.get("status", ""),
        "total": order.get("total", "0"),
        "currency": order.get("currency", "JPY"),
        "billing_name": f"{billing.get('last_name', '')} {billing.get('first_name', '')}".strip(),
        "billing_email": billing.get("email", ""),
        "items": items,
        "diagnosis_id": diagnosis_id or "なし",
    }


def woo_webhook():
    """WooCommerce Webhook エンドポイント"""
    try:
        order = request.get_json(force=True, silent=True)
        if not order:
            logger.warning("Webhook: リクエストボディが空です")
            return jsonify({"status": "empty request"}), 400

        order_id = order.get("id")
        if not order_id:
            logger.warning("Webhook: order_id が見つかりません")
            return jsonify({"status": "missing order_id"}), 400

        # 注文からdiagnosis_idを抽出
        diagnosis_id = _extract_diagnosis_id(order)

        # 注文データをスプレッドシートに記録
        data = {
            "order_id": order_id,
            "diagnosis_id": diagnosis_id or "",
            "created_at": order.get("date_created", ""),
        }
        try:
            add_order(data)
        except Exception as e:
            logger.error(f"Webhook: スプレッドシート書き込みエラー: {e}")

        # 管理者へメール通知
        try:
            order_summary = _build_order_summary_for_mail(order, diagnosis_id)
            send_order_mail(order_summary, diagnosis_id or f"order-{order_id}")
        except Exception as e:
            logger.warning(f"Webhook: メール通知送信失敗: {e}")

        # diagnosis_idがない場合（LINE経由でない直接購入）
        if not diagnosis_id:
            logger.info(
                f"Webhook: 注文 {order_id} はLINE経由でない直接購入です "
                f"(diagnosis_idなし)"
            )
            return jsonify({"status": "ok", "note": "no diagnosis_id, direct purchase"})

        # 診断結果を取得
        diagnosis = get_diagnosis(diagnosis_id)
        if not diagnosis:
            logger.warning(f"Webhook: diagnosis_id={diagnosis_id} が見つかりません")
            return jsonify({"status": "diagnosis not found"})

        # 購入済みフラグを更新
        try:
            mark_purchased(diagnosis_id)
        except Exception as e:
            logger.warning(f"Webhook: 購入済みフラグ更新失敗: {e}")

        # LINEユーザーにメッセージ送信
        # ※LINE未登録ユーザーの場合はスキップ
        # （LINE登録を購入の必須条件にすると購入機会の損失になるため）
        user_id = diagnosis.get("user_line_id")
        if not user_id:
            logger.info(
                f"Webhook: 診断 {diagnosis_id} のユーザーはLINE未登録です。"
                f"LINEメッセージ送信をスキップします。"
            )
            return jsonify({"status": "ok", "note": "user not registered on LINE"})

        stones = diagnosis.get("stones", "未定")
        message = (
            "ご注文ありがとうございます\n\n"
            f"使用する石: {stones}\n\n"
            "制作を開始します。"
        )

        success = push_line(user_id, message)
        if success:
            logger.info(f"Webhook: 注文 {order_id} の処理完了（LINE通知送信済み）")
        else:
            logger.warning(
                f"Webhook: 注文 {order_id} のLINE通知送信に失敗しました。"
                f"注文処理自体は正常に完了しています。"
            )

        return jsonify({"status": "ok"})

    except Exception as e:
        logger.exception("Webhook処理中にエラーが発生しました")
        return jsonify({"status": "error", "message": str(e)}), 500

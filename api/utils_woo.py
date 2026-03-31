"""WooCommerce商品情報取得モジュール

マッチング結果の上位商品に対してWooCommerce REST APIから
商品名・価格・画像・URLなどの販売情報を取得する。
"""

import os
import logging
import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


def _get_woo_credentials() -> tuple[str, str, str] | None:
    """WooCommerce API認証情報を環境変数から取得する"""
    base_url  = os.environ.get("WOO_BASE_URL", "").rstrip("/")
    key       = os.environ.get("WOO_CONSUMER_KEY", "")
    secret    = os.environ.get("WOO_CONSUMER_SECRET", "")

    if not base_url or not key or not secret:
        logger.warning("WooCommerce APIの環境変数が設定されていません")
        return None
    return base_url, key, secret


def fetch_woo_products(product_ids: list[int]) -> dict[int, dict]:
    """
    WooCommerce product_idのリストから商品詳細を取得する。

    戻り値: {product_id: {name, price, image_url, product_url}}
    取得失敗・未設定の場合は空dictを返す（診断は止めない）。
    """
    if not product_ids:
        return {}

    creds = _get_woo_credentials()
    if creds is None:
        return {}

    base_url, key, secret = creds
    auth = HTTPBasicAuth(key, secret)

    result: dict[int, dict] = {}

    for pid in product_ids:
        try:
            resp = requests.get(
                f"{base_url}/wp-json/wc/v3/products/{pid}",
                auth=auth,
                timeout=5,
            )
            if resp.status_code != 200:
                logger.warning("WooCommerce商品取得失敗: id=%s status=%s", pid, resp.status_code)
                continue

            data = resp.json()
            images = data.get("images") or []
            image_url = images[0].get("src", "") if images else ""

            result[pid] = {
                "name":        data.get("name", ""),
                "price":       data.get("price", ""),
                "image_url":   image_url,
                "product_url": data.get("permalink", ""),
                "stock_status": data.get("stock_status", ""),
            }
        except Exception as e:
            logger.warning("WooCommerce商品取得エラー: id=%s error=%s", pid, e)

    return result

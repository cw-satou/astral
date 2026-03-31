"""シートキャッシュユーティリティ

マスターデータ（石・組み合わせ・商品）をシートから取得する際の
TTL付きインメモリキャッシュを提供する。
"""

import time
import logging

logger = logging.getLogger(__name__)

CACHE_TTL = 300  # 5分


class SheetCache:
    """シート読み込み結果のTTL付きインメモリキャッシュ"""

    def __init__(self, name: str, ttl: float = CACHE_TTL):
        self._name = name
        self._ttl = ttl
        self._data: dict | None = None
        self._expires: float = 0.0

    def get(self) -> dict | None:
        """キャッシュが有効ならデータを返す。期限切れ・未設定はNone。"""
        if self._data is not None and time.time() < self._expires:
            logger.debug("キャッシュヒット: %s", self._name)
            return self._data
        return None

    def set(self, data: dict) -> None:
        """データをキャッシュに格納する"""
        self._data = data
        self._expires = time.time() + self._ttl
        logger.debug("キャッシュ更新: %s (%d件)", self._name, len(data))

    def invalidate(self) -> None:
        """キャッシュを破棄して次回アクセスで再読み込みさせる"""
        self._data = None
        self._expires = 0.0
        logger.info("キャッシュクリア: %s", self._name)

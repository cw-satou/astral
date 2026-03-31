"""役割重み定義

ブレスレット内の石の役割（main/sub/round）とサイズによる影響度を定義する。
商品特性の自動計算時に使用する。
"""

# ===== 役割×サイズ別の重み =====

ROLE_WEIGHT: dict[str, float] = {
    "main_12": 1.6,
    "main_10": 1.4,
    "main_8":  1.2,
    "sub_12":  1.3,
    "sub_10":  1.15,
    "sub_8":   1.05,
    "round_8": 1.0,
}

# ===== 組み合わせ時の役割ペアによる重み =====

COMBINATION_ROLE_WEIGHT: dict[str, float] = {
    "main_main":   1.2,
    "main_sub":    1.1,
    "main_round":  1.0,
    "sub_sub":     0.9,
    "sub_round":   0.8,
    "round_round": 0.6,
}


def get_role_weight(role: str, size: int) -> float:
    """役割とサイズから重みを取得する。該当なければ1.0を返す。"""
    key = f"{role}_{size}"
    return ROLE_WEIGHT.get(key, 1.0)


def get_combination_role_weight(role_a: str, role_b: str) -> float:
    """2つの石の役割ペアから組み合わせ重みを取得する。"""
    key = f"{role_a}_{role_b}"
    if key in COMBINATION_ROLE_WEIGHT:
        return COMBINATION_ROLE_WEIGHT[key]
    # 順序を逆にして再試行
    key_rev = f"{role_b}_{role_a}"
    return COMBINATION_ROLE_WEIGHT.get(key_rev, 1.0)

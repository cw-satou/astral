from typing import Dict, Any

def build_order_summary(
    diagnosis_result: Dict[str, Any],
    wrist_inner_cm: float,
    bead_size_mm: int
) -> Dict[str, str]:
    """
    diagnosis_result: PerplexityからのJSON(dictに変換済み)
    wrist_inner_cm: 手首の内径（cm）
    bead_size_mm: 使用する基本の石サイズ（mm）

    戻り値:
      {
        "order_line": "内径〇cm、アメジスト×15、ブルータイガーアイ×3",
        "internal_note": "ショップ用メモ",
        "sales_copy": "商品ページに載せる説明文"
      }
    """

    stones = diagnosis_result.get("stones", [])

    # 「アメジスト×15、ブルータイガーアイ×3」部分を作る
    stone_parts = []
    for s in stones:
        name = s.get("name", "不明な石")
        count = s.get("count", 0)
        stone_parts.append(f"{name}×{count}")
    stones_text = "、".join(stone_parts)

    # 表示用の1行（D1に近い形）
    order_line = f"内径{wrist_inner_cm}cm、{stones_text}"

    # ショップ側の内部メモ（デザイン意図などをまとめる）
    reading = diagnosis_result.get("reading", "")
    design_concept = diagnosis_result.get("design_concept", "無題")
    design_text = diagnosis_result.get("design_text", "")

    internal_note = (
        f"[占い要約]\n{reading}\n\n"
        f"[デザインコンセプト]\n{design_concept}\n"
        f"{design_text}\n\n"
        f"[仕様メモ]\n"
        f"- 手首内径: {wrist_inner_cm}cm\n"
        f"- 使用予定ビーズサイズ: {bead_size_mm}mm\n"
        f"- 石構成: {stones_text}\n"
    )

    # 販売ページにそのまま使える説明文
    sales_copy = diagnosis_result.get("sales_copy", "")
    if not sales_copy:
        sales_copy = (
            f"【{design_concept}】\n\n"
            f"{reading}\n\n"
            f"手首{wrist_inner_cm}cm前後の方向けに、{stones_text}でお作りするブレスレットです。"
        )

    return {
        "order_line": order_line,
        "internal_note": internal_note,
        "sales_copy": sales_copy,
    }

def build_admin_notification(line_user_id: str, order_summary: Dict[str, str]) -> str:
    return (
        "【新規オーダーが入りました】\n"
        f"- LINEユーザーID: {line_user_id}\n"
        f"- 注文内容: {order_summary['order_line']}\n\n"
        f"▼内部メモ\n{order_summary['internal_note']}"
    )

import os
import json
import gspread
from google.oauth2.service_account import Credentials

# スコープはそのままでOK（必要に応じて調整）
PROFILE_SHEET_NAME = "profiles"
LOG_SHEET_NAME = "diagnosis_logs"
ORDER_SHEET_NAME = "orders"
SCOPES = [
 "https://www.googleapis.com/auth/spreadsheets",
 "https://www.googleapis.com/auth/drive"
]
# ==========================
# Client生成
# ==========================
def get_client():
    service_account_info = json.loads(
        os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    )
    creds = Credentials.from_service_account_info(
        service_account_info,
        scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_log_sheet():
    client = get_client()
    sheet = client.open_by_key(
        os.environ["GOOGLE_SHEET_ID"]
    ).worksheet(LOG_SHEET_NAME)
    return sheet

def get_order_sheet():
    client = get_client()
    sh = client.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    return sh.worksheet(ORDER_SHEET_NAME)


def add_order(data: dict):
    sheet = get_order_sheet()

    row = [
        data.get("order_id", ""),
        data.get("diagnosis_id", ""),
        data.get("user_line_id", ""),
        data.get("product_slug", ""),
        data.get("stones", ""),
        data.get("wrist_inner_cm", ""),
        data.get("bead_size_mm", ""),
        data.get("bracelet_type", ""),
        data.get("order_status", "pending"),
        data.get("created_at", "")
    ]

    sheet.append_row(row, table_range="A1")
# ==========================
# 追加保存
# ==========================
def add_diagnosis(data: dict):
    sheet = get_log_sheet()

    row = [
        data.get("diagnosis_id", ""),
        data.get("created_at", ""),
        data.get("stone_name", ""),
        data.get("element_lack", ""),
        data.get("horoscope_full", ""),
        data.get("past", ""),
        data.get("present_future", ""),
        data.get("element_detail", ""),
        data.get("oracle_name", ""),
        data.get("oracle_position", ""),
        data.get("stones", ""),
        data.get("product_slug", ""),
        data.get("user_line_id",""),          # user_line_id
        False        # purchased
    ]

    sheet.append_row(row, table_range="A1")

def update_diagnosis(diagnosis_id: str, stones: str, product_slug: str):
    sheet = get_log_sheet()

    id_column = sheet.col_values(1)

    if diagnosis_id not in id_column:
        return

    row = id_column.index(diagnosis_id) + 1

    headers = sheet.row_values(1)

    stones_col = headers.index("stones") + 1
    slug_col = headers.index("product_slug") + 1

    sheet.update_cell(row, stones_col, stones)
    sheet.update_cell(row, slug_col, product_slug)

def mark_purchased(diagnosis_id: str):

    sheet = get_log_sheet()

    id_column = sheet.col_values(1)

    if diagnosis_id not in id_column:
        return

    row = id_column.index(diagnosis_id) + 1

    header = sheet.row_values(1)
    col_index = header.index("purchased") + 1

    sheet.update_cell(row, col_index, True)

def format_stones(stone_counts: dict):

    """
    {"アメジスト":2,"ローズ":14}
    ↓
    アメジスト×2,ローズ×14
    """

    parts = []

    for name, count in stone_counts.items():
        parts.append(f"{name}×{count}")

    return ",".join(parts)

# ==========================
# 1件取得（高速版）
# ==========================
def get_diagnosis(diagnosis_id: str):
    sheet = get_log_sheet()

    # 全行取得せず、1列目のみ取得
    id_column = sheet.col_values(1)

    if diagnosis_id not in id_column:
        return None

    row_index = id_column.index(diagnosis_id) + 1
    row_data = sheet.row_values(row_index)

    headers = sheet.row_values(1)

    return dict(zip(headers, row_data))


def get_profile_sheet():
    client = get_client()
    sh = client.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    ws = sh.worksheet(PROFILE_SHEET_NAME)

    return ws


def upsert_profile(profile: dict):
    """
    profile 例:
    {
      "user_id": "xxxx",
      "gender": "女性",
      "birth": {
          "date": "1990-01-01",
          "time": "12:00",
          "place": "札幌市"
      },
      "wrist_inner_cm": 15.0,
      "bead_size_mm": 8,
      "bracelet_type": "birth_top_element_side",
    }
    """
    client = get_client()
    sh = client.open_by_key(os.environ["GOOGLE_SHEET_ID"])
    ws = sh.worksheet(PROFILE_SHEET_NAME)

    # 1行目ヘッダー → 列名と列番号の対応を作る
    header = ws.row_values(1)
    col_index = {name: i + 1 for i, name in enumerate(header)}

    user_id = profile["user_id"]

    # birth をフラットに
    birth = profile.get("birth", {}) or {}
    birth_date = birth.get("date", "")
    birth_time = birth.get("time", "")
    birth_place = birth.get("place", "")

    # 1. user_id で既存行を探す（なければ新規）
    try:
        cell = ws.find(user_id)
        row = cell.row
    except Exception:
        row = len(ws.get_all_values()) + 1

    def set_cell(col_name, value):
        if col_name not in col_index:
            return
        col = col_index[col_name]
        ws.update_cell(row, col, value)

    set_cell("user_id", user_id)
    set_cell("gender", profile.get("gender", ""))
    set_cell("birth_date", birth_date)
    set_cell("birth_time", birth_time)
    set_cell("birth_place", birth_place)
    set_cell("wrist_inner_cm", profile.get("wrist_inner_cm", ""))
    set_cell("bead_size_mm", profile.get("bead_size_mm", ""))
    set_cell("bracelet_type", profile.get("bracelet_type", ""))


def get_profile(user_id: str):
    sheet = get_profile_sheet()

    id_column = sheet.col_values(1)  # A列
    if user_id not in id_column:
        return None

    row_index = id_column.index(user_id) + 1
    row_data = sheet.row_values(row_index)

    # ヘッダー行（1行目）を辞書キーとして使う
    headers = sheet.row_values(1)
    data = dict(zip(headers, row_data))

    # API で返しやすい形に整形
    return {
        "user_id": data.get("user_id"),
        "gender": data.get("gender"),
        "birth": {
            "date": data.get("birth_date"),
            "time": data.get("birth_time"),
            "place": data.get("birth_place"),
        },
        "wrist_inner_cm": float(data["wrist_inner_cm"]) if data.get("wrist_inner_cm") else None,
        "bead_size_mm": int(data["bead_size_mm"]) if data.get("bead_size_mm") else None,
        "bracelet_type": data.get("bracelet_type"),
    }

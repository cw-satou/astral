import os
import json
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


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


def get_sheet():
    client = get_client()
    sheet = client.open_by_key(
        os.environ["GOOGLE_SHEET_ID"]
    ).sheet1
    return sheet


# ==========================
# 追加保存
# ==========================
def add_diagnosis(data: dict):
    sheet = get_sheet()

    row = [
        data.get("diagnosis_id", ""),
        data.get("created_at", ""),
        data.get("stone_name", ""),
        data.get("element_lack", ""),
        data.get("horoscope_full", ""),
        data.get("past", ""),
        data.get("present", ""),
        data.get("future", ""),
        data.get("element_detail", ""),
        data.get("oracle_name", ""),
        data.get("oracle_position", ""),
        data.get("product_slug", ""),
        "",          # user_line_id
        False        # purchased
    ]

    sheet.append_row(row, value_input_option="USER_ENTERED")


# ==========================
# 1件取得（高速版）
# ==========================
def get_diagnosis(diagnosis_id: str):
    sheet = get_sheet()

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
    # スプレッドシート内の「プロフィール」シートを前提
    return client.open_by_key(
        os.environ["GOOGLE_SHEET_ID"]
    ).worksheet("プロフィール")

def upsert_profile(profile: dict):
    sheet = get_profile_sheet()

    user_id = profile["user_id"]
    birth = profile.get("birth") or {}

    # シートのヘッダー定義に合わせる（A1:H1 はあらかじめ自分で入れておく）
    # A: user_id
    # B: gender
    # C: birth_date
    # D: birth_time
    # E: birth_place
    # F: wrist_inner_cm
    # G: bead_size_mm
    # H: bracelet_type
    row = [
        user_id,
        profile.get("gender", ""),
        birth.get("date", ""),
        birth.get("time", ""),
        birth.get("place", ""),
        profile.get("wrist_inner_cm", ""),
        profile.get("bead_size_mm", ""),
        profile.get("bracelet_type", ""),
    ]

    # user_id が既にあるか確認
    id_column = sheet.col_values(1)  # A列
    if user_id in id_column:
        row_index = id_column.index(user_id) + 1  # 1始まり
        # 2行目以降を更新対象とする前提（ヘッダーは1行目）
        sheet.update(f"A{row_index}:H{row_index}", [row])
    else:
        sheet.append_row(row, value_input_option="USER_ENTERED")

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

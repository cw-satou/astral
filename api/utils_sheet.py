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
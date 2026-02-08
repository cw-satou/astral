import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# シート名（スプレッドシートの下のタブ名）
SHEET_NAME = "シート1" 
# ※もしスプレッドシート自体のIDで指定したい場合は .open_by_key() を使いますが、
# ここでは一番簡単な .open("スプレッドシートのファイル名") を想定します。
# 確実に動かすには「スプレッドシートキー（URLの/d/xxx/editのxxx部分）」を使うのがベストです。
SPREADSHEET_KEY = os.environ.get("SPREADSHEET_KEY") 

def save_to_sheet(user_data, ai_result, diagnosis_id):
    try:
        # 環境変数から認証情報を読み込む
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if not creds_json:
            print("Google Credentials not found.")
            return

        creds_dict = json.loads(creds_json)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # シートを開く
        if SPREADSHEET_KEY:
            sheet = client.open_by_key(SPREADSHEET_KEY).worksheet(SHEET_NAME)
        else:
            # キーがない場合は名前で探す（環境によって不安定なのでキー推奨）
            sheet = client.open("CustomerList").worksheet(SHEET_NAME)

        # 書き込むデータ（カラム順序に合わせて配列を作る）
        # 例: 日時, ID, 性別, 年齢(生年月日), 悩み, オラクルカード, 提案した石
        
        stones_str = ", ".join([f"{s['name']}({s['count']})" for s in ai_result.get('stones', [])])
        oracle = ai_result.get('oracle_card', {})
        oracle_str = f"{oracle.get('name')} ({'正' if oracle.get('is_upright') else '逆'})"
        
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            diagnosis_id,
            user_data.get('gender'),
            f"{user_data.get('birth', {}).get('date')} {user_data.get('birth', {}).get('time')}",
            user_data.get('birth', {}).get('place'),
            user_data.get('problem'), # カテゴリ+詳細が結合された文字列
            oracle_str,
            stones_str,
            ai_result.get('design_concept')
        ]
        
        sheet.append_row(row)
        print(f"Saved to sheet: {diagnosis_id}")

    except Exception as e:
        print(f"Sheet Error: {e}")

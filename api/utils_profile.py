# api/profile.py (Vercel serverless function)
import os
import json
from http import HTTPStatus

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build  # type: ignore

SPREADSHEET_ID = os.environ["SHEETS_SPREAD_ID"]
SHEET_NAME = "profiles"

def get_sheets_service():
    creds_json = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
    info = json.loads(creds_json)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return build("sheets", "v4", credentials=creds)

def find_row_index(service, user_id: str):
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A2:A"
    ).execute()
    values = result.get("values", [])
    for idx, row in enumerate(values, start=2):
        if row and row[0] == user_id:
            return idx
    return None

def upsert_profile(body: dict):
    service = get_sheets_service()
    sheet = service.spreadsheets()

    user_id = body["user_id"]
    birth = body.get("birth") or {}

    row = [
        user_id,
        body.get("gender", ""),
        birth.get("date", ""),
        birth.get("time", ""),
        birth.get("place", ""),
        body.get("wrist_inner_cm", ""),
        body.get("bead_size_mm", ""),
        body.get("bracelet_type", ""),
    ]

    row_index = find_row_index(service, user_id)
    if row_index:
        # UPDATE
        sheet.values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A{row_index}:H{row_index}",
            valueInputOption="RAW",
            body={"values": [row]},
        ).execute()
    else:
        # APPEND
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:H",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]},
        ).execute()

def get_profile(user_id: str):
    service = get_sheets_service()
    sheet = service.spreadsheets()
    row_index = find_row_index(service, user_id)
    if not row_index:
        return None

    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A{row_index}:H{row_index}",
    ).execute()
    values = result.get("values", [])
    if not values:
        return None
    r = values[0]
    return {
        "user_id": r[0],
        "gender": r[1] or None,
        "birth": {
            "date": r[2] or None,
            "time": r[3] or None,
            "place": r[4] or None,
        },
        "wrist_inner_cm": float(r[5]) if len(r) > 5 and r[5] else None,
        "bead_size_mm": int(r[6]) if len(r) > 6 and r[6] else None,
        "bracelet_type": r[7] if len(r) > 7 else None,
    }

def handler(request, response):
    if request.method == "POST":
        body = request.get_json()
        if not body or "user_id" not in body:
            response.status_code = HTTPStatus.BAD_REQUEST
            return response.send({"error": "user_id is required"})
        upsert_profile(body)
        profile = get_profile(body["user_id"])
        return response.send(profile)

    if request.method == "GET":
        user_id = request.args.get("user_id")
        if not user_id:
            response.status_code = HTTPStatus.BAD_REQUEST
            return response.send({"error": "user_id is required"})
        profile = get_profile(user_id)
        if not profile:
            response.status_code = HTTPStatus.NOT_FOUND
            return response.send({"error": "not found"})
        return response.send(profile)

    response.status_code = HTTPStatus.METHOD_NOT_ALLOWED
    return response.send({"error": "method not allowed"})

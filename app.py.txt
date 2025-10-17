from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os
import requests
import threading
import time

app = Flask(__name__)

# --- 環境変数から読み取る ---
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_JSON = os.getenv("CREDENTIALS_JSON")

# --- Google認証 ---
def get_client():
    creds_dict = json.loads(CREDENTIALS_JSON)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

# --- スプレッドシート監視 ---
def check_spreadsheet():
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).sheet1
    last_row = ""
    while True:
        data = sheet.get_all_values()
        if not data:
            time.sleep(60)
            continue
        new_last_row = str(data[-1])
        if new_last_row != last_row:
            last_row = new_last_row
            message = f"🆕 新しい行が追加されました:\n{', '.join(data[-1])}"
            requests.post(WEBHOOK_URL, json={"content": message})
        time.sleep(60)

@app.route('/')
def home():
    return "Bot is running!"

def run_checker():
    thread = threading.Thread(target=check_spreadsheet)
    thread.start()

if __name__ == '__main__':
    run_checker()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import requests
import threading
import time
import json

app = Flask(__name__)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_JSON = os.getenv("CREDENTIALS_JSON")

def check_spreadsheet():
    print("📊 Spreadsheetチェック開始")
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(CREDENTIALS_JSON), scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        last_row = sheet.get_all_values()[-1]
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return

    while True:
        try:
            data = sheet.get_all_values()
            if data[-1] != last_row:
                last_row = data[-1]
                message = f"✅ 新しい行が追加されました: {' , '.join(last_row)}"
                requests.post(WEBHOOK_URL, json={"content": message})
                print(f"📢 Discordへ通知送信: {message}")
            time.sleep(30)
        except Exception as e:
            print(f"⚠️ エラー発生: {e}")
            time.sleep(30)

@app.route('/')
def home():
    return "Bot is running and watching Google Sheets."

def run_checker():
    thread = threading.Thread(target=check_spreadsheet, daemon=True)
    thread.start()
    print("🚀 Spreadsheet監視スレッド開始")

import os, requests

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if WEBHOOK_URL:
    res = requests.post(WEBHOOK_URL, json={"content": "✅ Render起動テスト通知"})
    print("Discord通知テスト:", res.status_code)
else:
    print("❌ 環境変数 WEBHOOK_URL が見つかりません")


if __name__ == "__main__":
    run_checker()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

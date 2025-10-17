from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import os
import threading
import time

app = Flask(__name__)

import requests

try:
    r = requests.post(
        "https://discord.com/api/webhooks/1428405945259790369/ffR5MnNqs2P1RvBEkFe1GTPtp82AtGFGLokyKAO_vYe6DRVBJie-PYo7MlnJzf7xeLVz",
        json={"content": "✅ Discord通知テスト: Renderから送信しました"},
        timeout=10
    )
    print("Discord webhook status:", r.status_code)
except Exception as e:
    print("Discord通知エラー:", e)


WEBHOOK_URL = "https://discord.com/api/webhooks/1428405945259790369/ffR5MnNqs2P1RvBEkFe1GTPtp82AtGFGLokyKAO_vYe6DRVBJie-PYo7MlnJzf7xeLVz"
SHEET_ID = "16K2H535BZcHh8I0wjgnDh6EexmPusNblsuapD8kpRTU"

def check_spreadsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1

    last_row = ""
    while True:
        data = sheet.get_all_values()
        if data and data[-1] != last_row:
            last_row = data[-1]
            message = "新しい行が追加されました:\n" + ", ".join(last_row)
            requests.post(WEBHOOK_URL, json={"content": message})
        time.sleep(60)  # 1分ごとにチェック

@app.route('/')
def home():
    return "Bot is running!"

def run_checker():
    thread = threading.Thread(target=check_spreadsheet)
    thread.start()

if __name__ == "__main__":
    run_checker()
    app.run(host='0.0.0.0', port=10000)

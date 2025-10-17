from flask import Flask
import gspread
from google.oauth2.service_account import Credentials
import requests
import os
import threading
import time
import json

app = Flask(__name__)

# === 設定項目 ===
WEBHOOK_URL = "https://discord.com/api/webhooks/1428405945259790369/ffR5MnNqs2P1RvBEkFe1GTPtp82AtGFGLokyKAO_vYe6DRVBJie-PYo7MlnJzf7xeLVz"
SHEET_ID = "16K2H535BZcHh8I0wjgnDh6EexmPusNblsuapD8kpRTU"

# === Google認証 ===
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Renderの環境変数からJSONを読み取る
creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = Credentials.from_service_account_info(creds_info, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# === スプレッドシート監視 ===
last_row_data = None

def check_spreadsheet():
    global last_row_data
    while True:
        try:
            data = sheet.get_all_values()
            if not data:
                time.sleep(60)
                continue

            last_row = data[-1]  # 一番下の行
            if last_row != last_row_data:
                last_row_data = last_row
                message = f"🆕 新しい商品が追加されました！\n\n**内容:** {' | '.join(last_row)}"
                requests.post(WEBHOOK_URL, json={"content": message})
                print("通知を送信しました:", message)

            time.sleep(60)

        except Exception as e:
            print("スプレッドシート監視エラー:", e)
            time.sleep(60)

# === Flaskアプリ起動 ===
@app.route("/")
def home():
    return "✅ Bot is running!"

def run_checker():
    thread = threading.Thread(target=check_spreadsheet)
    thread.start()

if __name__ == "__main__":
    run_checker()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

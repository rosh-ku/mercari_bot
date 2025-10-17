from flask import Flask
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import os
import threading
import time

app = Flask(__name__)

WEBHOOK_URL = "https://discord.com/api/webhooks/1428405945259790369/ffR5MnNqs2P1RvBEkFe1GTPtp82AtGFGLokyKAO_vYe6DRVBJie-PYo7MlnJzf7xeLVz"
SHEET_ID = "16K2H535BZcHh8I0wjgnDh6EexmPusNblsuapD8kpRTU"

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

last_row_data = None

def check_spreadsheet():
    global last_row_data
    while True:
        try:
            data = sheet.get_all_values()
            if not data:
                time.sleep(60)
                continue

            last_row = data[-1]
            if last_row != last_row_data:
                last_row_data = last_row
                message = f"🆕 新しい商品が追加されました！\n\n**内容:** {' | '.join(last_row)}"
                requests.post(WEBHOOK_URL, json={"content": message})
                print("通知を送信しました:", message)

            time.sleep(60)

        except Exception as e:
            print("スプレッドシート監視エラー:", e)
            time.sleep(60)

@app.route("/")
def home():
    return "✅ Bot is running!"

def run_checker():
    thread = threading.Thread(target=check_spreadsheet)
    thread.start()

if __name__ == "__main__":
    run_checker()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

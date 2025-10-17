from flask import Flask
import os, json, requests, threading, time
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ==== 環境変数 ====
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_JSON = json.loads(os.getenv("CREDENTIALS_JSON"))

# ==== Google Sheets認証 ====
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(CREDENTIALS_JSON, scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

# ==== Discord通知関数 ====
def send_discord_message(content):
    try:
        res = requests.post(WEBHOOK_URL, json={"content": content})
        print(f"Discord通知送信: {res.status_code}")
    except Exception as e:
        print(f"Discord通知エラー: {e}")

# ==== スプレッドシート監視関数 ====
def check_spreadsheet():
    print("📊 スプレッドシート監視開始")
    last_row = None
    while True:
        try:
            data = sheet.get_all_values()
            if not data:
                continue

            new_row = data[-1]
            if new_row != last_row:
                last_row = new_row
                message = f"✅ 新しい行が追加されました: {' | '.join(new_row)}"
                send_discord_message(message)
        except Exception as e:
            print(f"⚠️ エラー発生: {e}")
        time.sleep(30)

# ==== Flaskルート ====
@app.route('/')
def home():
    return "Bot is running and watching Google Sheets."

# ==== メイン実行 ====
if __name__ == "__main__":
    # 起動通知
    send_discord_message("✅ Render起動テスト通知")

    # 監視スレッドを開始
    thread = threading.Thread(target=check_spreadsheet, daemon=True)
    thread.start()

    # Flask起動
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


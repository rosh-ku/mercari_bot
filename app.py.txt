from flask import Flask
from google.oauth2.service_account import Credentials
import gspread
import os, json, requests, threading, time
from bs4 import BeautifulSoup

app = Flask(__name__)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
SHEET_ID = os.getenv("SHEET_ID")
CREDENTIALS_JSON = os.getenv("CREDENTIALS_JSON")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(json.loads(CREDENTIALS_JSON), scopes=scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID).sheet1

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/114.0.0.0 Safari/537.36"
}

def notify_discord(msg):
    """Discordに通知"""
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": msg})
        except Exception as e:
            print("通知エラー:", e)

def check_item_status(url):
    """メルカリ商品ページの状態を判定"""
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 404:
            return "deleted"
        html = res.text
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()

        if any(word in text for word in ["削除されました", "出品が停止", "存在しない", "ページが見つかりません"]):
            return "deleted"
        elif any(word in text for word in ["SOLD", "売り切れ", "この商品は購入できません"]):
            return "sold"
        elif any(word in text for word in ["販売停止", "非公開", "現在表示できません"]):
            return "paused"
        else:
            return "active"
    except Exception as e:
        print("ステータス確認エラー:", e)
        return "error"

def check_spreadsheet():
    """スプレッドシート新規行検知"""
    print("📊 スプレッドシート監視開始（新規行）")
    prev_rows = len(sheet.get_all_values())
    while True:
        try:
            rows = sheet.get_all_values()
            if len(rows) > prev_rows:
                new_row = rows[-1]
                message = f"✅ 新しい行が追加されました: {' | '.join(new_row)}"
                notify_discord(message)
                prev_rows = len(rows)
        except Exception as e:
            print("⚠️ スプレッドシートエラー:", e)
        time.sleep(30)

def check_item_availability():
    """商品削除・売り切れ検知"""
    print("🕵️ 商品ステータス監視開始（削除・売り切れ対応）")
    checked = {}

    # 起動時：初期状態を記録のみ（通知はしない）
    data = sheet.get_all_values()
    for row in data[1:]:
        if row and row[0].startswith("http"):
            status = check_item_status(row[0])
            checked[row[0]] = status

    # 定期チェック
    while True:
        try:
            data = sheet.get_all_values()
            for row in data[1:]:
                if not row or not row[0].startswith("http"):
                    continue
                url = row[0]
                new_status = check_item_status(url)
                old_status = checked.get(url, "active")

                if old_status != new_status:
                    if new_status == "deleted":
                        notify_discord(f"❌ 商品削除検知: {url}")
                    elif new_status == "sold":
                        notify_discord(f"⚠️ 商品売り切れ検知: {url}")
                    elif new_status == "paused":
                        notify_discord(f"⚠️ 商品販売停止検知: {url}")

                checked[url] = new_status
        except Exception as e:
            print("削除・売り切れ検知エラー:", e)

        time.sleep(300)  # 5分ごと

@app.route('/')
def home():
    return "Bot is running (削除＋売り切れ検知モード)"

def run_checker():
    threading.Thread(target=check_spreadsheet, daemon=True).start()
    threading.Thread(target=check_item_availability, daemon=True).start()
    print("🤖 Bot起動完了（監視スレッド開始）")

if __name__ == '__main__':
    notify_discord("✅ Render起動通知（削除・売り切れ検知版）")
    run_checker()
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

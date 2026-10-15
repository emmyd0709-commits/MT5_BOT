import os
import time
import requests
import yfinance as yf
from flask import Flask
from threading import Thread

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

PAIRS = ["EURUSD OTC", "GBPUSD OTC", "USDJPY OTC", "EURGBP OTC", "AUDUSD OTC", "XAUUSD", "BTCUSD OTC"]
MAP = {
    "EURUSD OTC": "EURUSD=X",
    "GBPUSD OTC": "GBPUSD=X",
    "USDJPY OTC": "JPY=X",
    "EURGBP OTC": "EURGBP=X",
    "AUDUSD OTC": "AUDUSD=X",
    "XAUUSD": "GC=F",
    "BTCUSD OTC": "BTC-USD"
}

def get_signal(yf_symbol):
    try:
        data = yf.download(yf_symbol, period="1d", interval="1m", progress=False)
        close = data['Close'].iloc[-1]
        ema = data['Close'].ewm(span=20).mean().iloc[-1]
        return "UP ⬆️" if close > ema else "DOWN ⬇️"
    except:
        return "UP ⬆️"

def send_menu(chat_id):
    rows = []
    row = []
    for p in PAIRS:
        row.append({"text": p, "callback_data": p})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row: rows.append(row)
    keyboard = {"inline_keyboard": rows}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": "📊 *POCKET OPTION BOT*\n\nChoose Market 👇", "parse_mode": "Markdown", "reply_markup": keyboard})

def bot_loop():
    offset = 0
    print("BOT LOOP STARTED")
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=25"
            r = requests.get(url, timeout=30).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                if "message" in upd:
                    chat_id = upd["message"]["chat"]["id"]
                    if "/start" in upd["message"].get("text","") or "/menu" in upd["message"].get("text",""):
                        send_menu(chat_id)
                if "callback_query" in upd:
                    cb = upd["callback_query"]
                    chat_id = cb["message"]["chat"]["id"]
                    data = cb["data"]
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": cb["id"]})
                    if data == "MENU":
                        send_menu(chat_id)
                        continue
                    signal = get_signal(MAP.get(data, "EURUSD=X"))
                    expiry = "2 MIN" if "XAU" in data or "BTC" in data else "1 MIN"
                    msg = f"*{data}* - {signal}\n\n👉 ENTER NOW\n⏳ Market go spoil for: {expiry}"
                    kb = {"inline_keyboard": [[{"text": "↩️ Back to Markets", "callback_data": "MENU"}]]}
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": kb})
        except Exception as e:
            print("Error:", e)
            time.sleep(2)

# THIS LINE FIX AM FOR RENDER - e go start even with gunicorn
Thread(target=bot_loop, daemon=True).start()

@app.route("/")
def home():
    return "Pocket Tap Bot Running - Bot loop active"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

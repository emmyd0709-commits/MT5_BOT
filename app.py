import os
import time
import requests
import yfinance as yf
from flask import Flask
from threading import Thread

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Pocket Option markets
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
        if len(data) < 30:
            return "UP ⬆️"
        close = data['Close'].iloc[-1]
        ema = data['Close'].ewm(span=20).mean().iloc[-1]
        if close > ema:
            return "UP ⬆️"
        else:
            return "DOWN ⬇️"
    except:
        return "UP ⬆️"

def send_menu(chat_id):
    # 2 buttons per row for Pocket style
    rows = []
    row = []
    for p in PAIRS:
        row.append({"text": p, "callback_data": p})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    
    keyboard = {"inline_keyboard": rows}
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": chat_id,
        "text": "📊 *POCKET OPTION BOT*\n\nChoose Market 👇 Tap anyone to see signal",
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })

def bot_loop():
    offset = 0
    print("Bot started...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=25"
            r = requests.get(url, timeout=30).json()
            for upd in r.get("result", []):
                offset = upd["update_id"] + 1
                
                # When user sends /start
                if "message" in upd:
                    chat_id = upd["message"]["chat"]["id"]
                    txt = upd["message"].get("text", "")
                    if "/start" in txt or "/menu" in txt:
                        send_menu(chat_id)

                # When user taps button
                if "callback_query" in upd:
                    cb = upd["callback_query"]
                    chat_id = cb["message"]["chat"]["id"]
                    data = cb["data"]

                    # Answer the tap
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
                                  json={"callback_query_id": cb["id"]})

                    if data == "MENU":
                        send_menu(chat_id)
                        continue

                    # Get signal for tapped market
                    signal = get_signal(MAP.get(data, "EURUSD=X"))
                    expiry = "2 MIN" if "XAU" in data or "BTC" in data else "1 MIN"
                    
                    msg = f"*{data}* - {signal}\n\n👉 ENTER NOW\n⏳ Market go spoil for: {expiry}"
                    
                    kb = {"inline_keyboard": [[{"text": "↩️ Back to Markets", "callback_data": "MENU"}]]}
                    
                    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                                  json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "reply_markup": kb})
        except Exception as e:
            print("Error:", e)
            time.sleep(2)

@app.route("/")
def home():
    return "Pocket Tap Bot Running"

if __name__ == "__main__":
    Thread(target=bot_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

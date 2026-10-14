import time, requests, os
from flask import Flask
import yfinance as yf
import pandas as pd
import ta
from datetime import datetime

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "PUT_TOKEN_HERE")
CHAT_ID = os.getenv("CHAT_ID", "PUT_CHAT_ID_HERE")
PAIRS = ["EURUSD=X", "GBPUSD=X", "XAUUSD=X", "BTC-USD"]

def get_signal(pair):
    data = yf.download(pair, period="1d", interval="5m")
    if len(data) < 200:
        return None
    df = data.copy()
    close = df['Close']
    rsi = ta.momentum.RSIIndicator(close).rsi().iloc[-1]
    ema50 = ta.trend.EMAIndicator(close, 50).ema_indicator().iloc[-1]
    ema200 = ta.trend.EMAIndicator(close, 200).ema_indicator().iloc[-1]
    macd = ta.trend.MACD(close).macd_diff().iloc[-1]
    stoch = ta.momentum.StochasticOscillator(df['High'], df['Low'], close).stoch().iloc[-1]
    bb_high = ta.volatility.BollingerBands(close).bollinger_hband().iloc[-1]
    bb_low = ta.volatility.BollingerBands(close).bollinger_lband().iloc[-1]
    adx = ta.trend.ADXIndicator(df['High'], df['Low'], close).adx().iloc[-1]
    cci = ta.trend.CCIIndicator(df['High'], df['Low'], close).cci().iloc[-1]
    psar = ta.trend.PSARIndicator(df['High'], df['Low'], close).psar().iloc[-1]
    price = float(close.iloc[-1])
    votes_buy = 0
    votes_sell = 0
    if rsi < 35: votes_buy+=1
    elif rsi > 65: votes_sell+=1
    if price > ema50: votes_buy+=1
    else: votes_sell+=1
    if price > ema200: votes_buy+=1
    else: votes_sell+=1
    if macd > 0: votes_buy+=1
    else: votes_sell+=1
    if stoch < 20: votes_buy+=1
    elif stoch > 80: votes_sell+=1
    if price <= bb_low: votes_buy+=1
    elif price >= bb_high: votes_sell+=1
    if adx > 25 and price > ema50: votes_buy+=1
    elif adx > 25 and price < ema50: votes_sell+=1
    if cci < -100: votes_buy+=1
    elif cci > 100: votes_sell+=1
    if price > psar: votes_buy+=1
    else: votes_sell+=1
    if votes_buy >= 7:
        action = "BUY 📈 (Market Go Rise)"
        strength = int((votes_buy/10)*100)
        sl = price - (price*0.001)
        tp = price + (price*0.002)
    elif votes_sell >= 7:
        action = "SELL 📉 (Market Go Fall)"
        strength = int((votes_sell/10)*100)
        sl = price + (price*0.001)
        tp = price - (price*0.002)
    else:
        return None
    msg = f"🔥 MT5 10-INDICATOR SIGNAL 🔥\nPair: {pair.replace('=X','')}\nAction: {action}\nStrength: {strength}%\nPrice: {price:.5f}\nSL: {sl:.5f}\nTP: {tp:.5f}\nTime: {datetime.now().strftime('%H:%M:%S')}"
    return msg

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

@app.route('/')
def home():
    return "MT5 Bot Running!"

def run_bot():
    while True:
        for pair in PAIRS:
            sig = get_signal(pair)
            if sig:
                send_telegram(sig)
        time.sleep(60)

import threading
threading.Thread(target=run_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

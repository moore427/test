import requests
from datetime import datetime
import schedule
import threading
import time
from flask import Flask

# ===== 填入你的資料 =====
NEWS_API_KEY = "c8c11650703e417b9336b98c2e8083c0"
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"
CHAT_ID = 1094674922

# ===== DR 股票設定 =====
DR_STOCKS = {
    "台積電 DR": "2330.TW",
    "鴻海 DR": "2317.TW"
}

# ===== requests headers =====
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ===== 抓台股加權指數 =====
def get_tw_stock_index():
    try:
        date_str = datetime.now().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALL"
        r = requests.get(url, headers=HEADERS, verify=False)
        data = r.json()
        if "data5" in data:
            for row in data["data5"]:
                if "加權指數" in row:
                    index_price = row[1]
                    change = row[2]
                    percent = row[3]
                    return f"📈 台股加權指數: {index_price} ({change}, {percent})"
        return "❌ 無法取得台股加權指數"
    except Exception as e:
        return f"❌ 無法取得台股加權指數 ({e})"

# ===== 抓 DR 股票行情 =====
def get_dr_stocks():
    messages = []
    for name, symbol in DR_STOCKS.items():
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
            r = requests.get(url, headers=HEADERS, verify=False)
            data = r.json()
            quote = data["quoteResponse"]["result"][0]
            price = quote.get("regularMarketPrice", "N/A")
            change = quote.get("regularMarketChange", "N/A")
            percent = quote.get("regularMarketChangePercent", "N/A")
            messages.append(f"{name}: {price} ({change}, {percent}%)")
        except Exception as e:
            messages.append(f"{name}: ❌ 無法取得資料 ({e})")
    return "\n".join(messages)

# ===== 最新財經新聞 =====
def get_finance_news():
    try:
        url = f"https://newsapi.org/v2/everything?q=台股&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        r = requests.get(url, headers=HEADERS, verify=False)
        articles = r.json().get("articles", [])
        if not articles:
            return "❌ 無法取得"
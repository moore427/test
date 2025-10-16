import requests
from datetime import datetime
import schedule
import threading
import time
from flask import Flask

# ===== 填入你的資料 =====
BOT_TOKEN="8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"       # 從 @BotFather 拿
CHAT_ID = 1094674922   # 你的 Telegram Chat ID  
NEWS_API_KEY = "c8c11650703e417b9336b98c2e8083c0"

# ===== DR 股票設定 =====
DR_STOCKS = {
    "台積電 DR": "2330.TW",
    "鴻海 DR": "2317.TW"
}

# ===== 抓台股加權指數 =====
def get_tw_stock_index():
    try:
        date_str = datetime.now().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALL"
        r = requests.get(url)
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
            data = requests.get(url).json()
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
        url = f"https://newsapi.org/v2/top-headlines?country=tw&category=business&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        articles = response.json().get("articles", [])
        if not articles:
            return "❌ 無法取得新聞或新聞數量為0"
        headlines = [f"📰 {a['title']} ({a['source']['name']})" for a in articles[:5]]
        return "\n".join(headlines)
    except Exception as e:
        return f"❌ 無法取得新聞 ({e})"

# ===== 熱門漲跌股 =====
def get_top_stocks():
    try:
        date_str = datetime.now().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date={date_str}&type=ALL"
        r = requests.get(url)
        data = r.json()
        top_gainers = []
        top_losers = []

        if "data9" in data:
            for row in data["data9"][:5]:
                top_gainers.append(f"{row[0]} {row[1]} ({row[2]}%)")
        if "data10" in data:
            for row in data["data10"][:5]:
                top_losers.append(f"{row[0]} {row[1]} ({row[2]}%)")

        msg = "📈 漲幅前5名:\n" + "\n".join(top_gainers) + "\n\n"
        msg += "📉 跌幅前5名:\n" + "\n".join(top_losers)
        return msg
    except:
        return "❌ 無法取得熱門股票排行"

# ===== 融資融券變化 =====
def get_margin_trading():
    try:
        date_str = datetime.now().strftime("%Y%m%d")
        url = f"https://www.twse.com.tw/exchangeReport/MI_MARGN?response=json&date={date_str}&selectType=ALL"
        r = requests.get(url)
        data = r.json()
        top_finance = []
        top_short = []

        if "data" in data:
            for row in data["data"][:5]:
                top_finance.append(f"{row[0]} {row[1]} 融資增減: {row[8]}")
                top_short.append(f"{row[0]} {row[1]} 融券增減: {row[9]}")

        msg = "💰 融資買進前5名:\n" + "\n".join(top_finance) + "\n\n"
        msg += "📉 融券賣出前5名:\n" + "\n".join(top_short)
        return msg
    except:
        return "❌ 無法取得融資餘額"

# ===== 發送 Telegram 訊息 =====
def send_to_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        r = requests.post(url, data=data)
        print(r.json())
    except Exception as e:
        print(f"發送 Telegram 訊息錯誤: {e}")

# ===== 每日推播任務 =====
def job():
    index_msg = get_tw_stock_index()
    dr_msg = get_dr_stocks()
    news_msg = get_finance_news()
    top_stocks_msg = get_top_stocks()
    margin_msg = get_margin_trading()

    message = f"📅 今日台股摘要 ({datetime.now().strftime('%Y/%m/%d')})\n\n"
    message += f"{index_msg}\n\n{dr_msg}\n\n最新財經新聞:\n{news_msg}\n\n"
    message += f"{top_stocks_msg}\n\n{margin_msg}"

    send_to_telegram(message)
    print(f"[{datetime.now()}] 已發送完整台股摘要")

# ===== 排程每天 8 點 =====
def run_schedule():
    schedule.every().minute.at(":01").do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=run_schedule).start()

# ===== Flask Web Server =====
app = Flask(__name__)

@app.route("/")
def index():
    return "Telegram Finance Bot is running!"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
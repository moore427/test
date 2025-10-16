import requests
from datetime import datetime
import schedule
import time

# ===== 填入你的資料 =====
BOT_TOKEN = "fiancenews_bot"       # 從 @BotFather 拿
CHAT_ID = "736743966"         # 你的 Telegram Chat ID
NEWS_API_KEY = "你的NewsAPI金鑰"

# ===== 股票設定 =====
DR_STOCKS = {
    "台積電 DR": "2330",
    "鴻海 DR": "2317"
}

# ===== 函式定義 =====
def get_tw_stock_index():
    """抓台股加權指數（示範抓 Yahoo Finance API）"""
    try:
        url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=^TWII"
        data = requests.get(url).json()
        quote = data["quoteResponse"]["result"][0]
        price = quote["regularMarketPrice"]
        change = quote["regularMarketChange"]
        percent = quote["regularMarketChangePercent"]
        return f"📈 台股加權指數: {price:.2f} ({change:+.2f}, {percent:+.2f}%)"
    except:
        return "❌ 無法取得台股加權指數"

def get_dr_stocks():
    """抓 DR 股票行情（示範抓 Yahoo Finance API）"""
    messages = []
    for name, symbol in DR_STOCKS.items():
        try:
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}.TW"
            data = requests.get(url).json()
            quote = data["quoteResponse"]["result"][0]
            price = quote["regularMarketPrice"]
            change = quote["regularMarketChange"]
            percent = quote["regularMarketChangePercent"]
            messages.append(f"{name}: {price:.2f} ({change:+.2f}, {percent:+.2f}%)")
        except:
            messages.append(f"{name}: ❌ 無法取得資料")
    return "\n".join(messages)

def get_finance_news():
    """取得最新台灣股市新聞（前5則）"""
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=tw&category=business&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        articles = response.json().get("articles", [])
        headlines = [f"📰 {article['title']} ({article['source']['name']})" for article in articles[:5]]
        return "\n".join(headlines)
    except:
        return "❌ 無法取得新聞"

def send_to_telegram(msg):
    """發送訊息到 Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print(f"發送 Telegram 訊息錯誤: {e}")

def job():
    """每天推播任務"""
    index_msg = get_tw_stock_index()
    dr_msg = get_dr_stocks()
    news_msg = get_finance_news()

    message = f"📅 今日台股摘要 ({datetime.now().strftime('%Y/%m/%d')})\n\n"
    message += f"{index_msg}\n\n{dr_msg}\n\n最新財經新聞:\n{news_msg}"
    send_to_telegram(message)
    print(f"[{datetime.now()}] 已發送台股 + DR + 財經新聞摘要")

# ===== 排程每天 8 點 =====
schedule.every().day.at("08:00").do(job)

# ===== Background Worker 主迴圈 =====
while True:
    schedule.run_pending()
    time.sleep(30)

# ===== Flask Web Server =====
@app.route("/")
def index():
    return "Telegram Finance Bot is running!"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port
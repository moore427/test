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

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ===== 最新財經 & 國際新聞（去重、最多15則） =====
def get_finance_news():
    try:
        # 搜尋台股、經濟、國際新聞
        url = f"https://newsapi.org/v2/everything?q=台股 OR 經濟 OR 國際&sortBy=publishedAt&language=zh&apiKey={NEWS_API_KEY}"
        r = requests.get(url, headers=HEADERS, verify=False)
        articles = r.json().get("articles", [])
        if not articles:
            return "❌ 無法取得新聞或新聞數量為0"

        # 去掉重複來源，保留最新
        seen_sources = set()
        headlines = []
        for a in articles:
            source_name = a['source']['name']
            if source_name not in seen_sources:
                seen_sources.add(source_name)
                headlines.append(f"📰 {a['title']} ({source_name})")
            if len(headlines) >= 15:
                break

        # 每則新聞空行分隔
        return "\n\n".join(headlines)

    except:
        return "❌ 無法取得新聞"

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
    news_msg = get_finance_news()

    message = f"📅 今日財經 & 國際新聞 ({datetime.now().strftime('%Y/%m/%d')})\n\n"
    message += f"{news_msg}"

    send_to_telegram(message)
    print(f"[{datetime.now()}] 已發送新聞摘要")

# ===== 排程每天 8 點 =====
def run_schedule():
    schedule.every().hour.at(":00").do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)

threading.Thread(target=run_schedule).start()

# ===== Flask Web Server =====
app = Flask(__name__)

@app.route("/")
def index():
    return "Telegram Finance & International News Bot is running!"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
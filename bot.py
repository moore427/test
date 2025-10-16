import requests
from datetime import datetime
import schedule
import time

# ===== 填入你的資料 =====
BOT_TOKEN = "fiancenews_bot"       # 從 @BotFather 拿
CHAT_ID = "736743966"         # 你的 Telegram Chat ID
NEWS_API_KEY = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g" # 如果要抓 NewsAPI 的台股新聞

# ===== 定義函式 =====
def get_finance_news():
    """取得最新台灣股市新聞（前5則）"""
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=tw&category=business&apiKey={NEWS_API_KEY}"
        response = requests.get(url)
        articles = response.json().get("articles", [])
        headlines = [f"📰 {article['title']} ({article['source']['name']})" for article in articles[:5]]
        message = f"📅 今日台灣股市新聞摘要 ({datetime.now().strftime('%Y/%m/%d')})\n\n" + "\n".join(headlines)
        return message
    except Exception as e:
        return f"❌ 取得新聞時發生錯誤: {e}"

def send_to_telegram(msg):
    """發送訊息到 Telegram"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg}
        requests.post(url, data=data)
    except Exception as e:
        print(f"發送 Telegram 訊息錯誤: {e}")

def job():
    news = get_finance_news()
    send_to_telegram(news)
    print(f"[{datetime.now()}] 已發送台股新聞")

# ===== 排程每天 8 點 =====
schedule.every().day.at("08:00").do(job)

# ===== Render 需要程式一直運行 =====
while True:
    schedule.run_pending()
    time.sleep(30)
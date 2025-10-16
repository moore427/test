# 發送新聞摘要
news = get_finance_news()
send_to_telegram(news)

import schedule
import time

import requests
from datetime import datetime

# ===== 填入你的資料 =====
BOT_TOKEN = "你的BotToken"
CHAT_ID = "你的ChatID"
NEWS_API_KEY = "你的NewsAPI金鑰"

def get_finance_news():
    """取得最新台灣股市新聞"""
    url = f"https://newsapi.org/v2/top-headlines?country=tw&category=business&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    articles = response.json().get("articles", [])
    headlines = [f"{article['title']} ({article['source']['name']})" for article in articles[:5]]
    message = f"📅 今日台灣股市新聞摘要 ({datetime.now().strftime('%Y/%m/%d')})\n\n" + "\n".join(headlines)
    return message

def send_to_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)



def job():
    news = get_finance_news()
    send_to_telegram(news)
    print(f"[{datetime.now()}] 已發送台灣股市新聞")

schedule.every().day.at("08:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
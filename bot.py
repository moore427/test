import requests
from telegram import Bot
import os
import json

# ---------- 配置 ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g")
CHAT_ID = int(os.getenv("CHAT_ID", 1094674922))
CACHE_FILE = "sent_news.json"

bot = Bot(token=BOT_TOKEN)

# ---------- 讀取已推播新聞 ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, ensure_ascii=False)

# ---------- 抓取金十免費 JSON API ----------
def fetch_news():
    url = "https://cdn.jin10.com/datatool/market_calendar.json"
    response = requests.get(url)
    news_list = []

    if response.status_code == 200:
        data = response.json()
        for item in data[:20]:
            importance = item.get("importance", "")
            if importance.lower() in ["medium", "high"]:
                title = item.get("title", "")
                time = item.get("time", "")
                category = item.get("category", "未分類")
                link = "https://rili.jin10.com"
                news_list.append(f"[{category}] {time} {title}\n{link}")
    return news_list

# ---------- 發送 Telegram ----------
def send_news(news_list):
    cache = load_cache()
    new_items = []

    for news in news_list:
        if news not in cache:
            bot.send_message(chat_id=CHAT_ID, text=news)
            cache.add(news)
            new_items.append(news)
    
    if new_items:
        save_cache(cache)

# ---------- 主程式 ----------
if __name__ == "__main__":
    news_list = fetch_news()
    if news_list:
        send_news(news_list)
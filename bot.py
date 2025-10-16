import requests
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
import os
import json
from flask import Flask, request

# ---------- 配置 ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g")
CHAT_ID = int(os.getenv("CHAT_ID", 1094674922))
CACHE_FILE = "sent_news.json"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ---------- Dispatcher 處理 Webhook 更新 ----------
dispatcher = Dispatcher(bot=bot, update_queue=None, workers=0, use_context=True)

# ---------- 讀取/保存已推播新聞 ----------
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
                time_str = item.get("time", "")
                category = item.get("category", "未分類")
                link = "https://rili.jin10.com"
                news_list.append(f"[{category}] {time_str} {title}\n{link}")
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

# ---------- Telegram /webhook 路由 ----------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK"

# ---------- /health 路由 ----------
@app.route("/health")
def health():
    return "OK"

# ---------- 指令範例 ----------
def start(update, context):
    update.message.reply_text("Bot is running ✅")

dispatcher.add_handler(CommandHandler("start", start))

# ---------- 背景抓新聞任務 ----------
def background_job():
    import time
    while True:
        try:
            news_list = fetch_news()
            if news_list:
                send_news(news_list)
        except Exception as e:
            print("抓新聞出錯:", e)
        time.sleep(300)  # 每 5 分鐘抓一次

# ---------- 啟動程式 ----------
if __name__ == "__main__":
    import threading
    threading.Thread(target=background_job, daemon=True).start()
    # Flask 服務
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
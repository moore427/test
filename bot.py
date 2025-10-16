import requests
from bs4 import BeautifulSoup
import os
import json
import threading
import time
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------- 配置 ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g")
CHAT_ID = int(os.getenv("CHAT_ID", 1094674922))
CACHE_FILE = "sent_news.json"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ---------- 讀取/保存已推播新聞 ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, ensure_ascii=False)

# ---------- 爬取免費經濟新聞 ----------
def fetch_news(free_only=True):
    news_list = []
    try:
        # 使用公開免費網站爬蟲，示例抓經濟日曆事件
        url = "https://rili.jin10.com/"  # 金十公開頁面
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # 假設每條新聞在 <li class="event-item"> 裡面
            items = soup.select("li.event-item")
            for item in items[:20]:
                category = item.select_one(".event-category").text.strip() if item.select_one(".event-category") else "未分類"
                time_str = item.select_one(".event-time").text.strip() if item.select_one(".event-time") else ""
                title = item.select_one(".event-title").text.strip() if item.select_one(".event-title") else ""
                link = "https://rili.jin10.com"
                news_list.append(f"[{category}] {time_str} {title}\n{link}")
    except Exception as e:
        print("爬新聞失敗:", e)
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

# ---------- Telegram 指令 ----------
async def all_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news_list = fetch_news(free_only=False)
    if news_list:
        for news in news_list:
            await update.message.reply_text(news)
    else:
        await update.message.reply_text("目前沒有新新聞。")

async def free_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news_list = fetch_news(free_only=True)
    if news_list:
        for news in news_list:
            await update.message.reply_text(news)
    else:
        await update.message.reply_text("目前沒有免費新聞。")

async def summary_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news_list = fetch_news(free_only=True)
    if news_list:
        summary = "\n".join(news_list[:5])
        await update.message.reply_text(summary)
    else:
        await update.message.reply_text("目前沒有摘要新聞。")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "歡迎使用金十模擬 BOT！指令:\n/all - 全部新聞\n/free - 免費新聞\n/summary - 摘要新聞"
    await update.message.reply_text(text)

# ---------- 建立 Application ----------
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("all", all_news))
application.add_handler(CommandHandler("free", free_news))
application.add_handler(CommandHandler("summary", summary_news))

# ---------- Webhook 路由 ----------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return "OK"

# ---------- 健康檢查 ----------
@app.route("/health")
def health():
    return "OK"

@app.route("/")
def index():
    return "BOT is running ✅"

# ---------- 背景抓新聞任務 ----------
def background_job():
    while True:
        try:
            news_list = fetch_news(free_only=True)
            if news_list:
                send_news(news_list)
        except Exception as e:
            print("抓新聞出錯:", e)
        time.sleep(300)  # 每5分鐘抓一次

# ---------- 啟動 Flask Web Service ----------
if __name__ == "__main__":
    threading.Thread(target=background_job, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

import os
import json
import time
import threading
import feedparser
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from deep_translator import GoogleTranslator

# ---------- 配置 ----------
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"
CHAT_ID = 1094674922
CACHE_FILE = "sent_news.json"

bot = Bot(token=BOT_TOKEN)
app = Flask(__name__)

# ---------- 翻譯 ----------
def translate_to_chinese(text):
    try:
        return GoogleTranslator(source="auto", target="zh-TW").translate(text)
    except Exception:
        return text

# ---------- 快取 ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, ensure_ascii=False)

# ---------- 抓免費 RSS 財經新聞 ----------
def fetch_news(limit=5):
    feeds = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^TWII&region=TW&lang=zh-Hant-TW",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://www.reuters.com/business/rss",
    ]
    news_list = []
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit]:
                title = translate_to_chinese(entry.title)
                link = entry.link
                published = entry.get("published", "")
                news_list.append(f"📰 {published}\n{title}\n{link}")
        except Exception as e:
            print("抓取 RSS 錯誤:", e)
    return news_list

# ---------- 傳送新聞 ----------
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

# ---------- 指令 /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot 已啟動，將自動推播最新財經新聞。\n可用指令：/today 查看最新 5 則。")

# ---------- 指令 /today ----------
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news_list = fetch_news(limit=5)
    if news_list:
        await update.message.reply_text("📊 最新財經新聞：")
        for news in news_list:
            await update.message.reply_text(news)
    else:
        await update.message.reply_text("暫時沒有可用的新聞資料。")

# ---------- 應用初始化 ----------
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("today", today))

# ---------- Webhook ----------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put_nowait(update)
    return "OK"

@app.route("/")
def index():
    return "Bot is running."

# ---------- 背景推播 ----------
def background_job():
    while True:
        try:
            news_list = fetch_news(limit=3)
            if news_list:
                send_news(news_list)
        except Exception as e:
            print("背景抓新聞錯誤:", e)
        time.sleep(300)  # 每 5 分鐘

if __name__ == "__main__":
    threading.Thread(target=background_job, daemon=True).start()
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://test-81r2.onrender.com/{BOT_TOKEN}",
    )

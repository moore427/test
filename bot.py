import os
import json
import feedparser
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googletrans import Translator

# ---------- 配置 ----------
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"
CHAT_ID = 1094674922
CACHE_FILE = "sent_news.json"
RSS_URL = "https://www.investing.com/rss/news_25.rss"

translator = Translator()
bot = Bot(token=BOT_TOKEN)

# ---------- 讀取/保存已推播新聞 ----------
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(cache), f, ensure_ascii=False)

# ---------- 抓 RSS + 翻譯 ----------
def fetch_news(limit=5):
    news_list = []
    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries[:limit]:
        title = entry.get("title")
        link = entry.get("link")
        summary = entry.get("summary", "")
        try:
            title_cn = translator.translate(title, dest="zh-tw").text
            summary_cn = translator.translate(summary, dest="zh-tw").text
        except Exception:
            title_cn = title
            summary_cn = summary
        news_list.append(f"{title_cn}\n{summary_cn}\n{link}")
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
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news_list = fetch_news(limit=5)
    if news_list:
        for news in news_list:
            await update.message.reply_text(news)
    else:
        await update.message.reply_text("目前沒有最新新聞。")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "歡迎使用免費經濟新聞 BOT！\n指令:\n/today - 更新最新5筆新聞（自動翻譯中文）"
    await update.message.reply_text(text)

# ---------- 建立 Application ----------
application = ApplicationBuilder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("today", today))

# ---------- 背景抓新聞任務 ----------
async def background_job(context: ContextTypes.DEFAULT_TYPE):
    news_list = fetch_news(limit=5)
    if news_list:
        send_news(news_list)

# ---------- 設置 JobQueue ----------
job_queue = application.job_queue
job_queue.run_repeating(background_job, interval=300, first=10)

# ---------- 啟動 BOT Webhook ----------
if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://test-81r2.onrender.com/{BOT_TOKEN}"
    )

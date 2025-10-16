import os
import asyncio
import requests
import feedparser
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from datetime import datetime, timedelta, timezone

# === 基本設定 ===
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"
CHAT_ID = 1094674922

# === 資料來源 ===
RSS_URLS = [
    "https://rss.cnn.com/rss/edition_business.rss",
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://www.reutersagency.com/feed/?best-topics=markets",
    "https://www.investing.com/rss/news_25.rss"
]

# === 取得新聞 ===
def fetch_latest_news(limit=5):
    news_items = []
    for url in RSS_URLS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                published = entry.get("published", "未知時間")
                news_items.append((published, title, link))
        except Exception as e:
            print(f"⚠️ 讀取 {url} 時出錯：{e}")

    # 依時間排序
    news_items.sort(reverse=True, key=lambda x: x[0])
    return news_items[:limit]

# === /today 指令 ===
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    news = fetch_latest_news()
    if not news:
        await update.message.reply_text("😿 目前無法取得最新新聞。")
        return

    msg = "📰 今日最新 5 筆市場消息：\n\n"
    for pub, title, link in news:
        msg += f"• {title}\n📅 {pub}\n🔗 {link}\n\n"
    await update.message.reply_text(msg)

# === 背景自動更新 ===
async def background_job(context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    news = fetch_latest_news()
    if news:
        msg = "⏰ 定時更新：最新市場消息\n\n"
        for pub, title, link in news:
            msg += f"• {title}\n📅 {pub}\n🔗 {link}\n\n"
        await bot.send_message(chat_id=CHAT_ID, text=msg)

# === 啟動成功通知 ===
async def send_startup_message():
    bot = Bot(token=BOT_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="✅ Bot 已成功啟動並在 Render 運行中！")

# === 主程式 ===
if __name__ == "__main__":
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # 指令註冊
    application.add_handler(CommandHandler("today", today))

    # 背景任務（每 5 分鐘）
    job_queue = application.job_queue
    job_queue.run_repeating(background_job, interval=300, first=10)

    # 啟動成功通知
    asyncio.run(send_startup_message())

    # 啟動 webhook (Render 用)
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        url_path=BOT_TOKEN,
        webhook_url=f"https://test-81r2.onrender.com/{BOT_TOKEN}"
    )

    # 若在本機測試請改用以下：
    # application.run_polling()

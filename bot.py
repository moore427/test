import feedparser
import json
import os
import time
import threading
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googletrans import Translator

# ---------- 配置 ----------
BOT_TOKEN = os.getenv("BOT_TOKEN", "你的BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID", 123456789))
CACHE_FILE = "sent_news.json"
RSS_URL = "https://www.investing.com/rss/news_25.rss"  # 全球經濟新聞RSS

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
            new

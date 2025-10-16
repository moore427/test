import requests
import time
import os
import feedparser
from flask import Flask, request
from threading import Thread
from googletrans import Translator  # pip install googletrans==4.0.0-rc1

# === 設定 ===
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"
CHAT_ID = 1094674922

app = Flask(__name__)
sent_econ_events = set()  # 已推播經濟事件
sent_titles = set()       # /today 去重新聞

translator = Translator()

# === 翻譯英文到中文 ===
def translate_to_chinese(text):
    try:
        result = translator.translate(text, dest='zh-tw')
        return result.text
    except Exception as e:
        print(f"❌ 翻譯失敗: {e}")
        return text

# === Telegram 發送訊息 ===
def send_message(text, reply_markup=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    requests.post(url, json=data)

# === 抓取即時經濟事件（Investing.com RSS）===
def fetch_econ_events():
    rss_url = "https://www.investing.com/rss/news.rss"
    events = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:
            if entry.title not in sent_econ_events:
                sent_econ_events.add(entry.title)
                short_link = entry.link.replace("https://", "").replace("http://", "")
                title_cn = translate_to_chinese(entry.title)  # 翻成中文
                events.append({
                    "title": title_cn,
                    "link": short_link,
                    "time": entry.published
                })
    except Exception as e:
        print(f"❌ 經濟事件抓取錯誤: {e}")
    return events

# === 即時推播經濟事件 ===
def realtime_push_econ():
    while True:
        events = fetch_econ_events()
        for e in events:
            msg = f"⚡ <b>{e['title']}</b>\n🔗 {e['link']}\n🕒 {e['time']}"
            send_message(msg)
            time.sleep(2)
        time.sleep(300)  # 每 5 分鐘抓一次

# === /today 指令 + 按鈕功能 ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"]
        if text == "/today":
            today_news = fetch_econ_events()
            if not today_news:
                send_message("❌ 暫無最新新聞")
            else:
                msg = "📅 今日重點摘要\n\n"
                for idx, n in enumerate(today_news[:5]):
                    if idx == 0:
                        msg += f"⚡ <b>{n['title']}</b>\n🔗 {n['link']}\n\n"
                    else:
                        msg += f"⚡ {n['title']}\n🔗 {n['link']}\n\n"
                reply_markup = {
                    "inline_keyboard": [[{"text": "刷新今日摘要", "callback_data": "/today"}]]
                }
                send_message(msg, reply_markup=reply_markup)
        else:
            send_message("📊 輸入 /today 或點擊按鈕可查看今日摘要")

    if "callback_query" in data:
        callback = data["callback_query"]
        if callback["data"] == "/today":
            today_news = fetch_econ_events()
            if not today_news:
                send_message("❌ 暫無最新新聞")
            else:
                msg = "📅 今日重點摘要\n\n"
                for idx, n in enumerate(today_news[:5]):
                    if idx == 0:
                        msg += f"⚡ <b>{n['title']}</b>\n🔗 {n['link']}\n\n"
                    else:
                        msg += f"⚡ {n['title']}\n🔗 {n['link']}\n\n"
                reply_markup = {
                    "inline_keyboard": [[{"text": "刷新今日摘要", "callback_data": "/today"}]]
                }
                send_message(msg, reply_markup=reply_markup)
    return "OK"

@app.route('/')
def home():
    return "✅ Finance News Bot Running!"

# === 啟動程式 ===
if __name__ == '__main__':
    Thread(target=realtime_push_econ).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
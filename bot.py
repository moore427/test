import requests
import time
import datetime
import os
import feedparser
from flask import Flask, request
from threading import Thread

# === 設定 ===
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"
CHAT_ID = 1094674922
NEWS_API_KEY = "c8c11650703e417b9336b98c2e8083c0"

app = Flask(__name__)
sent_titles = set()  # 記錄已推播的新聞


# === Telegram 發送訊息 ===
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


# === 新聞分類 ===
def classify_news(title):
    if any(k in title for k in ["台股", "台積電", "鴻海", "ETF", "權值股"]):
        return "📈【台股】"
    elif any(k in title for k in ["美股", "道瓊", "那斯達克", "標普", "FED", "美元"]):
        return "💵【美股】"
    elif any(k in title for k in ["中國", "日圓", "亞洲", "歐洲", "俄羅斯", "戰爭"]):
        return "🌏【國際】"
    elif any(k in title for k in ["AI", "晶片", "半導體", "科技", "蘋果", "輝達", "NVIDIA"]):
        return "🤖【科技】"
    elif any(k in title for k in ["通膨", "利率", "油價", "經濟", "物價", "景氣"]):
        return "📊【經濟】"
    else:
        return "📰【新聞】"


# === 抓取 RSS 中文新聞 ===
def fetch_rss_news():
    sources = {
        "Yahoo奇摩財經": "https://tw.stock.yahoo.com/rss",
        "自由時報": "https://news.ltn.com.tw/rss/business.xml",
        "中央社": "https://www.cna.com.tw/rss.aspx",
        "ETtoday": "https://www.ettoday.net/rss/business.xml"
    }
    articles = []
    for name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:5]:
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": name,
                    "category": classify_news(entry.title)
                })
        except Exception as e:
            print(f"❌ 無法解析 {name}: {e}")
    return articles


# === 抓取 NewsAPI 國際新聞（中文） ===
def fetch_newsapi():
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=zh,tw&apiKey={NEWS_API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        if data.get("status") == "ok":
            articles = []
            for a in data["articles"]:
                articles.append({
                    "title": a["title"],
                    "link": a["url"],
                    "source": a["source"]["name"],
                    "category": classify_news(a["title"])
                })
            return articles
    except Exception as e:
        print(f"❌ NewsAPI 錯誤: {e}")
    return []


# === 合併新聞來源 + 避免重複 ===
def get_all_news():
    rss = fetch_rss_news()
    api = fetch_newsapi()
    all_news = rss + api
    new_items = []
    for n in all_news:
        if n["title"] not in sent_titles:
            sent_titles.add(n["title"])
            new_items.append(n)
    return new_items


# === 即時推播（有新新聞就立刻發） ===
def realtime_push():
    while True:
        news = get_all_news()
        if news:
            for n in news:
                msg = f"{n['category']} <b>{n['title']}</b>\n來源：{n['source']}\n🔗 {n['link']}"
                send_message(msg)
                time.sleep(2)
        time.sleep(30)  # 每 30 秒檢查一次新新聞


# === /today 指令 ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"]
        if text == "/today":
            today_news = get_all_news()
            if not today_news:
                send_message("❌ 暫無最新新聞")
            else:
                msg = "📅 今日重點摘要\n\n"
                for n in today_news[:5]:
                    msg += f"{n['category']} {n['title']}\n來源：{n['source']}\n🔗 {n['link']}\n\n"
                send_message(msg)
        else:
            send_message("📊 輸入 /today 可查看今日摘要")
    return "OK"


@app.route('/')
def home():
    return "✅ Finance News Bot Running!"


# === 啟動程式 ===
if __name__ == '__main__':
    Thread(target=realtime_push).start()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
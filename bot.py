import requests
import time
import datetime
import threading
from flask import Flask, request
import schedule

# === 基本設定 ===
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"
CHAT_ID = 1094674922
NEWS_API_KEY = "c8c11650703e417b9336b98c2e8083c0"

app = Flask(__name__)
sent_titles = set()

# === 根據關鍵字分類 ===
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


# === 抓取中文新聞 ===
def fetch_news():
    urls = [
        f"https://newsapi.org/v2/top-headlines?language=zh&category=business&apiKey={NEWS_API_KEY}",
        f"https://newsapi.org/v2/top-headlines?language=zh&category=general&apiKey={NEWS_API_KEY}",
    ]
    articles = []
    for url in urls:
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            if data.get("status") == "ok":
                for a in data.get("articles", []):
                    title = a.get("title", "")
                    source = a.get("source", {}).get("name", "")
                    if (
                        title
                        and title not in sent_titles
                        and any(kw in title for kw in ["台股", "美股", "經濟", "通膨", "中國", "能源", "戰爭", "國際", "AI", "半導體", "科技", "ETF", "貨幣"])
                    ):
                        sent_titles.add(title)
                        a["category"] = classify_news(title)
                        articles.append(a)
        except Exception as e:
            print(f"❌ 抓取新聞錯誤: {e}")
    return articles


# === 股市指數 ===
def get_index():
    try:
        tw = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/^TWII").json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
        dj = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/^DJI").json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
        ndx = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/^IXIC").json()["chart"]["result"][0]["meta"]["regularMarketPrice"]
        return f"📈 台股加權：{tw}\n📉 道瓊工業：{dj}\n💹 那斯達克：{ndx}"
    except Exception as e:
        return f"❌ 無法取得指數 ({e})"


# === 發送訊息 ===
def send_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})


# === 即時新聞推播 ===
def realtime_job():
    while True:
        news = fetch_news()
        if news:
            print(f"🆕 有 {len(news)} 則新新聞")
            for n in news:
                title = n["title"]
                source = n["source"]["name"]
                link = n["url"]
                category = n.get("category", "📰【新聞】")
                published = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
                msg = f"🕓 {published}\n{category} <b>{title}</b>\n📡 來源：{source}\n🔗 {link}"
                send_message(msg)
                time.sleep(2)
        else:
            print("⏳ 沒有新新聞")
        time.sleep(60)


# === 每日早報 ===
def daily_summary():
    today = datetime.datetime.now().strftime("%Y/%m/%d")
    index_info = get_index()
    news = fetch_news()
    summary = "\n\n".join([f"{n['category']} {n['title']} ({n['source']['name']})" for n in news[:5]]) or "❌ 暫無新聞"
    msg = f"📅 今日重點摘要 ({today})\n\n{index_info}\n\n📰 最新新聞：\n{summary}"
    send_message(msg)
    print("✅ 已發送每日摘要")


# === Telegram 指令處理 ===
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        if text.lower() == "/today":
            daily_summary()
        else:
            send_message("📊 輸入 /today 可查看今日財經摘要")
    return "OK"


# === 排程每日早報 ===
def schedule_jobs():
    schedule.every().day.at("08:00").do(daily_summary)
    while True:
        schedule.run_pending()
        time.sleep(30)


@app.route('/')
def home():
    return "📡 即時新聞 + 每日早報 Bot 正在運作中"


if __name__ == '__main__':
    threading.Thread(target=realtime_job).start()
    threading.Thread(target=schedule_jobs).start()
    app.run(host='0.0.0.0', port=10000)
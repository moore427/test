import requests

# ===== 填入你的資料 =====
BOT_TOKEN = "8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"       # 從 @BotFather 拿
CHAT_ID = "736743966"         # 你的 Telegram Chat ID


def send_to_telegram(msg):
    """立即發送訊息到 Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    r = requests.post(url, data=data)
    print(r.json())  # 查看回傳結果，確認是否成功

# ===== 測試訊息 =====
send_to_telegram("✅ Telegram Bot 測試成功！")
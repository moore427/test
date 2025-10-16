
import requests

# ===== 填入你的 Bot Token =====
BOT_TOKEN ="8430406960:AAHP4EahpoxGeAsLZNDUdvH7RBTSYt4mT8g"

def get_updates():
    """抓取 Bot 的最新訊息更新"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    r = requests.get(url)
    data = r.json()
    return data

def main():
    updates = get_updates()
    if not updates.get("result"):
        print("⚠️ 沒有收到訊息，請先在 Telegram 發送任意訊息給 Bot")
        return

    print("✅ 已抓到最近訊息，以下是 Chat ID：\n")
    for u in updates["result"]:
        chat = u["message"]["chat"]
        print(f"使用者/群組名稱: {chat.get('first_name', chat.get('title','未知'))}")
        print(f"Chat ID: {chat['id']}")
        print("-" * 30)

    # 選擇第一個 Chat ID 發送測試訊息
    test_chat_id = updates["result"][0]["message"]["chat"]["id"]
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": test_chat_id, "text": "✅ 測試訊息成功！"}
    resp = requests.post(url, data=data)
    print(f"\n發送測試訊息結果: {resp.json()}")

if __name__ == "__main__":
    main()
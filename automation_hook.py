import requests
import time
import os

# Configuration: এন্টারপ্রাইজ স্ট্যান্ডার্ড এনভায়রনমেন্ট ভেরিয়েবল ব্যবহার করুন
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8763555298:AAFFzH0LqoQFLy0SB_lvyvF1cG0JhOBxwsQ")
CHAT_ID = os.getenv("CHAT_ID", "5819816252")
API_URL = "http://localhost:8000/transcreate"


def send_telegram(text, parse_mode="Markdown"):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}
    return requests.post(url, json=payload)


def main():
    print("[System]: Vocal Core Listener Active...")
    offset = 0

    while True:
        try:
            # Telegram Polling
            updates_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(updates_url, timeout=40).json()

            if response.get("result"):
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    message = update.get("message", {})
                    text = message.get("text")
                    chat_id = message.get("chat", {}).get("id")

                    if text:
                        # User-কে প্রসেসিং স্ট্যাটাস পাঠানো
                        send_telegram(
                            "⏳ *Vocal Core*: প্রসেসিং হচ্ছে...", "Markdown")

                        # API কল এবং এরর হ্যান্ডলিং
                        try:
                            api_resp = requests.post(
                                API_URL, json={"text": text}, timeout=120)
                            if api_resp.status_code == 200:
                                formatted = api_resp.json().get('formatted_text', 'No content')
                                send_telegram(
                                    f"🎙 *Transcreated Output:*\n\n{formatted}", "Markdown")
                            else:
                                send_telegram(
                                    "❌ *Error*: ভোকাল কোর ইঞ্জিন বর্তমানে সাড়া দিচ্ছে না।")
                        except Exception as e:
                            send_telegram(f"❌ *Engine Error*: {str(e)}")

        except Exception as e:
            print(f"[Network Error]: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()

import os
import time
import requests

TELEGRAM_TOKEN = os.getenv(
    "TELEGRAM_TOKEN", "8763555298:AAFFzH0LqoQFLy0SB_lvyvF1cG0JhOBxwsQ")
CHAT_ID = os.getenv("CHAT_ID", "5819816252")
API_URL = os.getenv("VOCAL_CORE_API_URL", "http://localhost:8000/transcreate")
TELEGRAM_API_BASE = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
REQUEST_TIMEOUT = 20
TELEGRAM_REQUEST_TIMEOUT = 35
POLL_TIMEOUT = 30
STATUS_MESSAGE = "⏳ Processing..."
OFFLINE_MESSAGE = "🎙 Vocal Core Engine is currently offline. Please try again later."


def sanitize_message(text):
    if not text:
        return ""
    cleaned = []
    previous_space = False
    for char in text.strip():
        if char in "\r\n\t":
            char = " "
        if ord(char) < 32 and char != " ":
            continue
        if char == " ":
            if previous_space:
                continue
            previous_space = True
            cleaned.append(char)
            continue
        previous_space = False
        cleaned.append(char)
    return "".join(cleaned).strip()


def telegram_api(method, payload=None, use_get=False):
    url = f"{TELEGRAM_API_BASE}/{method}"
    try:
        if use_get:
            response = requests.get(
                url, params=payload, timeout=TELEGRAM_REQUEST_TIMEOUT)
        else:
            response = requests.post(
                url, json=payload, timeout=TELEGRAM_REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        if not data.get("ok", False):
            raise RuntimeError(
                data.get("description", "Telegram API request failed"))
        return data["result"]
    except Exception as exc:
        print(f"[Telegram Error] {exc}")
        return None


def send_telegram_message(chat_id, message, reply_to_message_id=None):
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    if reply_to_message_id is not None:
        payload["reply_to_message_id"] = reply_to_message_id
    return telegram_api("sendMessage", payload)


def edit_telegram_message(chat_id, message_id, message):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    return telegram_api("editMessageText", payload)


def fetch_updates(offset):
    payload = {
        "timeout": POLL_TIMEOUT,
        "offset": offset,
        "allowed_updates": ["message"],
    }
    return telegram_api("getUpdates", payload, use_get=True) or []


def process_text(text):
    try:
        response = requests.post(
            API_URL, json={"text": text}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        result = data.get("formatted_text") or data.get("result") or ""
        if not result:
            raise RuntimeError("Vocal Core API returned an empty response")
        return result
    except requests.RequestException as exc:
        print(f"[Vocal Core Error] {exc}")
        return None
    except Exception as exc:
        print(f"[Vocal Core Error] {exc}")
        return None


def handle_message(message):
    chat = message.get("chat", {})
    chat_id = str(chat.get("id", ""))
    text = sanitize_message(message.get("text", ""))
    if not text:
        return
    if CHAT_ID and CHAT_ID != "PASTE_CHAT_ID_HERE" and chat_id != str(CHAT_ID):
        return

    status_message = send_telegram_message(
        chat_id, STATUS_MESSAGE, message.get("message_id"))
    result = process_text(text)

    if result is None:
        offline_text = f"*{OFFLINE_MESSAGE}*"
        if status_message and status_message.get("message_id"):
            edited = edit_telegram_message(
                chat_id, status_message["message_id"], offline_text)
            if edited is None:
                send_telegram_message(
                    chat_id, offline_text, message.get("message_id"))
        else:
            send_telegram_message(chat_id, offline_text,
                                  message.get("message_id"))
        return

    formatted_output = "*🎙 Vocal Core Output:*\n\n" + result
    if status_message and status_message.get("message_id"):
        edited = edit_telegram_message(
            chat_id, status_message["message_id"], formatted_output)
        if edited is None:
            send_telegram_message(chat_id, formatted_output,
                                  message.get("message_id"))
    else:
        send_telegram_message(chat_id, formatted_output,
                              message.get("message_id"))


def main():
    if TELEGRAM_TOKEN == "PASTE_TELEGRAM_BOT_TOKEN_HERE" or CHAT_ID == "PASTE_CHAT_ID_HERE":
        print("[System] Set TELEGRAM_TOKEN and CHAT_ID before running the bot.")
        return

    print("[System] Vocal Core Telegram Bot online. Polling for updates...")
    offset = 0

    while True:
        try:
            updates = fetch_updates(offset)
            for update in updates:
                update_id = update.get("update_id")
                if update_id is not None:
                    offset = update_id + 1
                message = update.get("message") or update.get("edited_message")
                if message:
                    handle_message(message)
        except Exception as exc:
            print(f"[System Error] {exc}")
            time.sleep(3)


if __name__ == "__main__":
    main()
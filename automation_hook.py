import logging
import os
import re
import signal
import time

import requests

# Configuration: এন্টারপ্রাইজ স্ট্যান্ডার্ড এনভায়রনমেন্ট ভেরিয়েবল ব্যবহার করুন
TELEGRAM_TOKEN = os.getenv("8763555298:AAHnxh6voGcWueEg_xyATAbO7XZNTRY0gA0")
CHAT_ID = os.getenv("5819816252")
API_URL = os.getenv("API_URL", "http://localhost:8000/transcreate")
API_AUTH_TOKEN = os.getenv("VOCAL_CORE_API_TOKEN")
POLL_BACKOFF_BASE = float(os.getenv("POLL_BACKOFF_BASE", "2"))
POLL_BACKOFF_MAX = float(os.getenv("POLL_BACKOFF_MAX", "30"))
ENGINE_MAX_RETRIES = int(os.getenv("ENGINE_MAX_RETRIES", "3"))
ENGINE_BACKOFF_BASE = float(os.getenv("ENGINE_BACKOFF_BASE", "1"))
ENGINE_BACKOFF_MAX = float(os.getenv("ENGINE_BACKOFF_MAX", "8"))
HEALTH_LOG_INTERVAL_SECONDS = int(
    os.getenv("HEALTH_LOG_INTERVAL_SECONDS", "300"))
LOGGER = logging.getLogger("automation_hook")


def send_telegram(session, token, chat_id, text, parse_mode=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    response = session.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response


def api_headers():
    headers = {}
    if API_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {API_AUTH_TOKEN}"
    return headers


def redact_sensitive(text):
    if not text:
        return text

    redacted = str(text)
    if TELEGRAM_TOKEN:
        redacted = redacted.replace(TELEGRAM_TOKEN, "[REDACTED_TOKEN]")
    if API_AUTH_TOKEN:
        redacted = redacted.replace(API_AUTH_TOKEN, "[REDACTED_TOKEN]")

    # Telegram bot token-like pattern: 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ
    redacted = re.sub(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b",
                      "[REDACTED_TOKEN]", redacted)
    return redacted


def backoff_delay(attempt, base_delay, max_delay):
    return min(max_delay, base_delay * (2 ** max(attempt - 1, 0)))


def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN environment variable is required")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    LOGGER.info("Vocal Core Listener Active")

    stop_requested = False

    def _request_stop(signum, _frame):
        nonlocal stop_requested
        stop_requested = True
        LOGGER.info("Shutdown signal received: %s", signum)

    signal.signal(signal.SIGINT, _request_stop)
    signal.signal(signal.SIGTERM, _request_stop)

    offset = 0
    poll_error_count = 0
    poll_errors_total = 0
    processed_messages = 0
    engine_retry_total = 0
    engine_failures_total = 0
    engine_parse_errors_total = 0
    start_time = time.monotonic()
    last_health_log_at = start_time
    session = requests.Session()

    def maybe_log_health(force=False):
        nonlocal last_health_log_at
        if HEALTH_LOG_INTERVAL_SECONDS <= 0 and not force:
            return

        now = time.monotonic()
        if not force and (now - last_health_log_at) < HEALTH_LOG_INTERVAL_SECONDS:
            return

        uptime_seconds = int(now - start_time)
        LOGGER.info(
            (
                "Health | uptime=%ss processed_messages=%s poll_errors_total=%s "
                "engine_retries_total=%s engine_failures_total=%s engine_parse_errors_total=%s"
            ),
            uptime_seconds,
            processed_messages,
            poll_errors_total,
            engine_retry_total,
            engine_failures_total,
            engine_parse_errors_total,
        )
        last_health_log_at = now

    try:
        while not stop_requested:
            try:
                # Telegram Polling
                updates_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
                response = session.get(
                    updates_url,
                    params={"offset": offset, "timeout": 30},
                    timeout=40,
                )
                response.raise_for_status()
                data = response.json()
                poll_error_count = 0

                if data.get("result"):
                    for update in data["result"]:
                        offset = update["update_id"] + 1
                        message = update.get("message", {})
                        text = (message.get("text") or "").strip()
                        chat_id = message.get("chat", {}).get("id")

                        if not chat_id or not text:
                            continue

                        # Optional allow-list: if CHAT_ID is set, only process that chat.
                        if CHAT_ID and str(chat_id) != str(CHAT_ID):
                            continue

                        # User-কে প্রসেসিং স্ট্যাটাস পাঠানো
                        processed_messages += 1
                        send_telegram(
                            session,
                            TELEGRAM_TOKEN,
                            chat_id,
                            "⏳ *Vocal Core*: প্রসেসিং হচ্ছে...",
                            "Markdown",
                        )

                        # API কল এবং এরর হ্যান্ডলিং
                        delivered = False
                        for attempt in range(1, ENGINE_MAX_RETRIES + 1):
                            try:
                                api_resp = session.post(
                                    API_URL,
                                    json={"text": text},
                                    headers=api_headers(),
                                    timeout=120,
                                )
                                api_resp.raise_for_status()
                                formatted = api_resp.json().get("formatted_text", "No content")

                                # Dynamic user content may break Markdown parsing, so plain text is safer.
                                send_telegram(
                                    session,
                                    TELEGRAM_TOKEN,
                                    chat_id,
                                    f"Transcreated Output:\n\n{formatted}",
                                    None,
                                )
                                delivered = True
                                break
                            except ValueError:
                                engine_parse_errors_total += 1
                                send_telegram(
                                    session,
                                    TELEGRAM_TOKEN,
                                    chat_id,
                                    "❌ Engine response parse failed.",
                                    None,
                                )
                                delivered = True
                                break
                            except requests.RequestException as e:
                                if attempt >= ENGINE_MAX_RETRIES:
                                    engine_failures_total += 1
                                    send_telegram(
                                        session,
                                        TELEGRAM_TOKEN,
                                        chat_id,
                                        "❌ Engine error: failed after multiple retries.",
                                        None,
                                    )
                                    LOGGER.warning(
                                        "Engine request failed after %s attempts: %s",
                                        ENGINE_MAX_RETRIES,
                                        redact_sensitive(e),
                                    )
                                else:
                                    engine_retry_total += 1
                                    delay = backoff_delay(
                                        attempt, ENGINE_BACKOFF_BASE, ENGINE_BACKOFF_MAX
                                    )
                                    time.sleep(delay)

                        if not delivered:
                            LOGGER.warning(
                                "Engine response was not delivered to chat %s", chat_id)
                maybe_log_health()
            except requests.RequestException as e:
                poll_error_count += 1
                poll_errors_total += 1
                delay = backoff_delay(
                    poll_error_count, POLL_BACKOFF_BASE, POLL_BACKOFF_MAX)
                LOGGER.warning(
                    "Network error while polling Telegram: %s", redact_sensitive(e))
                maybe_log_health()
                time.sleep(delay)
            except Exception:
                LOGGER.exception("Unexpected error in listener loop")
                maybe_log_health()
                time.sleep(5)
    finally:
        maybe_log_health(force=True)
        session.close()
        LOGGER.info("Listener stopped")


if __name__ == "__main__":
    main()

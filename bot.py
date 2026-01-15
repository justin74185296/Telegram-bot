import json
import logging
import os
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.telegram.org/bot{token}/{method}"
LONG_POLL_TIMEOUT = 30
NETWORK_BACKOFF = 3


def _api_request(token, method, params=None, timeout=LONG_POLL_TIMEOUT):
    url = API_BASE.format(token=token, method=method)
    data = urlencode(params or {}).encode("utf-8")
    request = Request(url, data=data)
    with urlopen(request, timeout=timeout + 10) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("ok"):
        raise RuntimeError(f"Telegram API error: {payload}")
    return payload.get("result", [])


def get_updates(token, offset=None):
    params = {"timeout": LONG_POLL_TIMEOUT}
    if offset is not None:
        params["offset"] = offset
    return _api_request(token, "getUpdates", params=params)


def send_message(token, chat_id, text, reply_to_message_id=None):
    params = {"chat_id": chat_id, "text": text}
    if reply_to_message_id is not None:
        params["reply_to_message_id"] = reply_to_message_id
    _api_request(token, "sendMessage", params=params, timeout=10)


def build_reply(text):
    if not text:
        return "I received your message."
    if text.startswith("/start"):
        return "Bot is running. Send me a message."
    return f"Received: {text}"


def run_bot(token):
    offset = None
    while True:
        try:
            updates = get_updates(token, offset=offset)
            for update in updates:
                offset = update.get("update_id", 0) + 1
                message = update.get("message") or update.get("edited_message")
                if not message:
                    continue
                chat_id = message["chat"]["id"]
                reply_text = build_reply(message.get("text", ""))
                send_message(
                    token,
                    chat_id,
                    reply_text,
                    reply_to_message_id=message.get("message_id"),
                )
        except (URLError, HTTPError, TimeoutError) as exc:
            logging.warning("Network error: %s", exc)
            time.sleep(NETWORK_BACKOFF)
        except Exception as exc:
            logging.exception("Unexpected error: %s", exc)
            time.sleep(NETWORK_BACKOFF)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Missing TELEGRAM_BOT_TOKEN environment variable.", file=sys.stderr)
        return 1
    run_bot(token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

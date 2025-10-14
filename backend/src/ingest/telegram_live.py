from __future__ import annotations

import asyncio
import logging
import os
import random
import time

import aiohttp
from telethon import TelegramClient, events

from ..infra.metrics import TG_LAST_MESSAGE_TS, TG_LAST_SCORE_OK_TS, TG_RECONNECTS_TOTAL

API_ID = int(os.getenv("TELEGRAM_API_ID", "0") or "0")
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION = os.getenv("TELEGRAM_SESSION", "backend/data/telegram.session")
CHANNELS = [
    x.strip() for x in os.getenv("TELEGRAM_CHANNELS", "").split(",") if x.strip()
]
MINLEN = int(os.getenv("TELEGRAM_MIN_TEXT_LEN", "12"))
API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)
log = logging.getLogger("tg-live")


def _jittered_sleep(attempt: int) -> float:
    base = float(os.getenv("TG_BACKOFF_BASE", "2"))
    mx = float(os.getenv("TG_BACKOFF_MAX_SEC", "60"))
    jitter = float(os.getenv("TG_BACKOFF_JITTER", "0.3"))
    raw = min(mx, (base**attempt))
    delta = raw * jitter
    return max(1.0, raw - delta + random.random() * (2 * delta))


async def score_and_route(
    text: str, source: str = "telegram", channel: str = ""
) -> None:
    """Call /signals/ingest-and-score API endpoint."""
    url = f"{API_BASE}/signals/ingest-and-score"
    timeout = aiohttp.ClientTimeout(
        total=float(os.getenv("TG_FETCH_TIMEOUT_SEC", "15"))
    )
    async with aiohttp.ClientSession(timeout=timeout) as s:
        try:
            async with s.post(
                url, params={"text": text, "source": source, "channel": channel}
            ) as r:
                j = await r.json()
                TG_LAST_SCORE_OK_TS.set(time.time())
                routed = j.get("routed", False)
                score = j.get("score", {})
                label = score.get("label", "?")
                conf = score.get("confidence", 0.0)
                log.info("scored: routed=%s label=%s conf=%.2f", routed, label, conf)
        except Exception as e:
            log.warning("score/route failed: %s", e)


async def run_once():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()
    log.info("Telegram client started")

    if CHANNELS:
        for ch in CHANNELS:
            try:
                await client.get_entity(ch)
                log.info("listening: %s", ch)
            except Exception as e:
                log.warning("failed to get entity %s: %s", ch, e)
    else:
        log.info("no TELEGRAM_CHANNELS set; listening to all messages")

    @client.on(events.NewMessage(chats=CHANNELS if CHANNELS else None))
    async def handler(ev):
        text = (ev.raw_text or "").strip()
        if len(text) < MINLEN:
            return
        TG_LAST_MESSAGE_TS.set(time.time())
        ch_name = ""
        try:
            chat = await ev.get_chat()
            if getattr(chat, "username", None):
                ch_name = "@" + chat.username
        except Exception:
            ch_name = ""
        log.info("message: %s...", text[:80])
        await score_and_route(text, source="telegram", channel=ch_name)

    log.info("tg live running… (Ctrl+C to stop)")
    await client.run_until_disconnected()


async def main():
    if API_ID == 0 or not API_HASH:
        raise SystemExit("TELEGRAM_API_ID/HASH missing in ENV")
    attempt = 0
    while True:
        try:
            await run_once()
            attempt = 0
        except Exception as e:
            attempt += 1
            TG_RECONNECTS_TOTAL.inc()
            sleep_s = _jittered_sleep(attempt)
            log.warning(
                "tg live crashed (%s). reconnecting in %.1fs (attempt=%d)…",
                e,
                sleep_s,
                attempt,
            )
            await asyncio.sleep(sleep_s)


if __name__ == "__main__":
    asyncio.run(main())

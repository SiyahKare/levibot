from __future__ import annotations

import asyncio
import datetime as dt
import os
import re
from typing import Any

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message

from ..infra.logger import log_event

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# Basit kalıp: SYMBOL side entry/sl/tp
PATTERN = re.compile(
    r"(?P<sym>[A-Z]{3,5}\/?USDT)\s+"
    r"(?P<side>LONG|SHORT|BUY|SELL)\b[\s\S]*?"
    r"(?:entry|ent|e)[:\s]*?(?P<entry>\d+[\.]?\d*)?[^\n]*?"
    r"(?:sl|stop)[:\s]*?(?P<sl>\d+[\.]?\d*)?[^\n]*?"
    r"(?:tp\d?|take)[:\s]*?(?P<tp>\d+[\.]?\d*)?",
    re.I,
)


def norm_symbol(s: str) -> str:
    s = (s or "").upper().replace("/", "")
    return s if s.endswith("USDT") else (s + "USDT" if s else s)


def _to_float(x: str | None) -> float | None:
    try:
        return float(x) if x else None
    except Exception:
        return None


def parse_signal(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    m = PATTERN.search(text)
    if not m:
        return None
    gd = m.groupdict()
    raw_side = (gd.get("side") or "").upper()
    side = (
        "LONG"
        if raw_side in ("LONG", "BUY")
        else "SHORT" if raw_side in ("SHORT", "SELL") else None
    )
    sym = norm_symbol(gd.get("sym") or "")
    if not sym or not side:
        return None
    return {
        "symbol": sym,
        "side": side,
        "entry": _to_float(gd.get("entry")),
        "sl": _to_float(gd.get("sl")),
        "tp": _to_float(gd.get("tp")),
    }


async def on_message(msg: Message) -> None:
    if not msg.text:
        return
    sig = parse_signal(msg.text)
    if not sig:
        return
    event_payload = {
        "group_id": msg.chat.id if msg.chat else None,
        "group_title": msg.chat.title if msg.chat else None,
        "message_id": msg.message_id,
        "text": msg.text[:2000],
        "signal": sig,
        "ts": dt.datetime.utcnow().isoformat() + "Z",
    }
    log_event("SIGNAL_EXT_TELEGRAM", event_payload, symbol=sig.get("symbol"))


def build_bot() -> tuple[Bot, Dispatcher]:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN env değişkeni gerekli")
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.message.register(on_message, F.text)
    return bot, dp


async def run_polling() -> None:
    bot, dp = build_bot()
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(run_polling())

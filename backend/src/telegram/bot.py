from __future__ import annotations

import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
import httpx

API_BASE = os.getenv("LEVI_API_BASE", "http://127.0.0.1:8000")


def _allowed_users() -> set[int]:
    raw = os.getenv("LEVI_TELEGRAM_USER_IDS", "")
    return {int(x) for x in raw.split(",") if x.strip().isdigit()}


async def handle_start(message: Message) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/start", json={})
    await message.answer("LeviBot: Başlatıldı. ETH liderliğinde altseason radar açık.")


async def handle_stop(message: Message) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/stop", json={"reason": "telegram"})
    await message.answer("LeviBot: Durduruldu. Tüm pozisyonlar takipte.")


async def handle_status(message: Message) -> None:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{API_BASE}/status")
        data = r.json()
    await message.answer(
        f"Running: {data['running']}\nOpen: {data['open_positions']}\nDD: {data.get('daily_dd_pct')}\n"
    )


async def handle_set_leverage(message: Message) -> None:
    try:
        parts = message.text.split()
        leverage = int(parts[-1])
    except Exception:
        await message.answer("Kullanım: /setleverage 3")
        return
    user_id = os.getenv("LEVI_DEFAULT_USER_ID", "onur")
    async with httpx.AsyncClient() as client:
        await client.post(f"{API_BASE}/risk/leverage", json={"user_id": user_id, "leverage": leverage})
    await message.answer(f"Kaldıraç ayarlandı: x{leverage}")


async def main() -> None:
    token = os.getenv("LEVI_TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("LEVI_TELEGRAM_BOT_TOKEN env eksik")
    bot = Bot(token=token)
    dp = Dispatcher()

    dp.message.register(handle_start, Command(commands=["start"]))
    dp.message.register(handle_stop, Command(commands=["stop"]))
    dp.message.register(handle_status, Command(commands=["status"]))
    dp.message.register(handle_set_leverage, Command(commands=["set", "setleverage"]))

    await dp.start_polling(bot, allowed_updates=["message"])


if __name__ == "__main__":
    asyncio.run(main())



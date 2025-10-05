import os
import asyncio
from aiogram import Bot


_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
_CHAT = os.getenv("TELEGRAM_ALERT_CHAT_ID")


async def _send_async(text: str):
    if not (_TOKEN and _CHAT):
        return
    bot = Bot(_TOKEN)
    try:
        await bot.send_message(_CHAT, text, disable_web_page_preview=True)
    finally:
        await bot.session.close()


def send(text: str):
    try:
        asyncio.get_running_loop()
        asyncio.create_task(_send_async(text))
    except RuntimeError:
        asyncio.run(_send_async(text))

















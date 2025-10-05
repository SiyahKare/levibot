import asyncio, datetime as dt, hashlib
from typing import List
from telethon import TelegramClient, events, types
from .config import (
    API_ID, API_HASH, SESSION_PATH,
    ALLOWED, AUTO_DISCOVER, INCLUDE_DM,
    STARTUP_HISTORY_LIMIT,
)
from .registry import load_checkpoints, save_checkpoints, is_allowed_by_patterns
from .signal_parser import parse_signal
from backend.src.infra.logger import log_event


def _fp(chat_id: int, msg_id: int, text: str) -> str:
    return hashlib.sha1(f"{chat_id}:{msg_id}:{text[:64]}".encode()).hexdigest()


async def discover_chats(client: TelegramClient) -> List[types.Dialog]:
    dialogs: List[types.Dialog] = []
    async for d in client.iter_dialogs():
        ent = d.entity
        is_group = isinstance(ent, (types.Chat, types.Channel)) and (
            getattr(ent, "megagroup", True) or getattr(ent, "broadcast", True)
        )
        is_dm = isinstance(ent, types.User)
        if is_dm and not INCLUDE_DM:
            continue

        username = getattr(ent, "username", None)
        title = getattr(ent, "title", "") or getattr(ent, "first_name", "") or ""
        cid = d.id

        if ALLOWED and (str(cid) in ALLOWED or (username and f"@{username}" in ALLOWED)):
            dialogs.append(d)
            continue

        if AUTO_DISCOVER and is_group and is_allowed_by_patterns(title, username):
            dialogs.append(d)
            continue

    return dialogs


async def backfill_chat(client: TelegramClient, dialog: types.Dialog, cp: dict):
    cid = dialog.id
    last_id = int(cp.get(str(cid), 0))
    count = 0
    async for msg in client.iter_messages(dialog.entity, limit=STARTUP_HISTORY_LIMIT):
        if msg.id <= last_id:
            break
        text = msg.raw_text or ""
        sig = parse_signal(text)
        if not sig:
            continue
        event = {
            "chat_id": cid,
            "chat_title": getattr(dialog.entity, "title", "") or getattr(dialog.entity, "username", ""),
            "message_id": msg.id,
            "text": text[:2000],
            "signal": sig,
            "ts": (msg.date or dt.datetime.utcnow()).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fp": _fp(cid, msg.id, text),
            "source": "backfill",
        }
        log_event("SIGNAL_EXT_TELEGRAM", event, symbol=sig.get("symbol"))
        count += 1
        cp[str(cid)] = max(last_id, msg.id)
    if count:
        save_checkpoints(cp)


async def run_ingest():
    client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
    await client.start()

    dialogs = await discover_chats(client)
    titles = [(d.id, getattr(d.entity, "title", "") or getattr(d.entity, "username", "")) for d in dialogs]
    log_event("TELEGRAM_DISCOVERY", {"count": len(titles), "chats": titles})

    cp = load_checkpoints()
    for d in dialogs:
        try:
            await backfill_chat(client, d, cp)
        except Exception as e:
            log_event("ERROR", {"scope": "telegram_backfill", "chat_id": d.id, "err": str(e)})

    @client.on(events.NewMessage(chats=[d.entity for d in dialogs]))
    async def handler(event):
        chat = await event.get_chat()
        title = getattr(chat, "title", "") or getattr(chat, "username", "")
        text = event.raw_text or ""
        sig = parse_signal(text)
        if not sig:
            return
        payload = {
            "chat_id": event.chat_id,
            "chat_title": title,
            "message_id": event.id,
            "text": text[:2000],
            "signal": sig,
            "ts": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fp": _fp(event.chat_id, event.id, text),
            "source": "live",
        }
        log_event("SIGNAL_EXT_TELEGRAM", payload, symbol=sig.get("symbol"))
        cid = str(event.chat_id)
        cp[cid] = max(int(cp.get(cid, 0)), event.id)
        save_checkpoints(cp)

    @client.on(events.ChatAction())
    async def on_join(e):
        me = await client.get_me()
        if e.user_joined or e.user_added:
            if any(u.id == me.id for u in e.users):
                log_event("TELEGRAM_JOINED_NEW", {"chat_id": e.chat_id})

    print("Telethon user-bot ingest running (auto-discover + backfill)…")
    await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(run_ingest())



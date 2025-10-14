"""
Telethon Live Listener - User Session
Listens to all joined Telegram groups and streams messages to JSONL/Redis
"""
import asyncio
import hashlib
import json
import os
import re
import signal
import time
from datetime import UTC
from pathlib import Path

from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, PhoneCodeInvalidError
from telethon.tl.types import MessageEntityUrl

# Configuration
API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")
SESSION = os.getenv("TG_SESSION_NAME", "levibot_user")
PHONE = os.getenv("TG_PHONE", "")
WATCH = [x.strip() for x in os.getenv("TG_WATCH_LIST", "").split(",") if x.strip()]

# Paths
DATA_DIR = Path("backend/data")
SESS_DIR = DATA_DIR / "telethon_session"
LOG_DIR = DATA_DIR / "logs/telethon"
LOG_DIR.mkdir(parents=True, exist_ok=True)
OUT_LOG = LOG_DIR / f"stream_{int(time.time())}.jsonl"

# Redis (optional)
R = None
try:
    import redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        R = redis.from_url(redis_url)
except Exception:
    pass

# Initialize client
SESS_DIR.mkdir(parents=True, exist_ok=True)
client = TelegramClient(str(SESS_DIR / SESSION), API_ID, API_HASH)

# URL regex
URL_RE = re.compile(r"https?://\S+")


def md5(s: str) -> str:
    """MD5 hash for deduplication."""
    return hashlib.md5(s.encode()).hexdigest()


def to_doc(msg, chat_name: str) -> dict:
    """Convert Telegram message to document."""
    text = msg.message or ""
    urls = URL_RE.findall(text)
    
    # Extract URLs from entities
    if msg.entities:
        urls += [
            e.url
            for e in msg.entities
            if isinstance(e, MessageEntityUrl) and getattr(e, "url", None)
        ]
    
    doc = {
        "id": msg.id,
        "chat": chat_name,
        "chat_id": msg.chat_id,
        "date": msg.date.astimezone(UTC).isoformat(),
        "from_id": (
            getattr(msg.from_id, "user_id", None)
            if hasattr(msg, "from_id")
            else None
        ),
        "text": text,
        "reply_to": getattr(msg, "reply_to_msg_id", None),
        "fwd_from": bool(getattr(msg, "fwd_from", None)),
        "urls": list(set(urls)),
        "edited": bool(msg.edit_date),
        "edit_date": (
            msg.edit_date.astimezone(UTC).isoformat()
            if msg.edit_date
            else None
        ),
        "media": bool(msg.media),
        "hash": md5(f"{msg.chat_id}:{msg.id}:{text[:128]}"),
        "ts_epoch": int(msg.date.replace(tzinfo=UTC).timestamp()),
    }
    return doc


async def produce(doc: dict):
    """Write document to JSONL and/or Redis."""
    line = json.dumps(doc, ensure_ascii=False)
    
    # Write to JSONL
    with OUT_LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    
    # Write to Redis (if configured)
    if R:
        try:
            R.xadd("telethon:stream", {"json": line})
        except Exception:
            pass  # Redis write failed, continue


_watch_cache = None
_watch_cache_time = 0


async def resolve_watch():
    """
    Return set of entity ids to watch.
    If WATCH empty, return all joined dialogs.
    """
    global _watch_cache, _watch_cache_time
    
    # Cache for 5 minutes
    if _watch_cache and (time.time() - _watch_cache_time) < 300:
        return _watch_cache
    
    targets = set()
    
    if WATCH:
        # Watch specific groups
        for w in WATCH:
            try:
                ent = await client.get_entity(w)
                targets.add(ent.id)
            except Exception:
                pass
    else:
        # Watch all joined dialogs
        async for d in client.iter_dialogs():
            if d.is_group or d.is_channel:
                targets.add(d.entity.id)
    
    _watch_cache = targets
    _watch_cache_time = time.time()
    return targets


@client.on(events.NewMessage)
async def handler(event):
    """Handle new messages."""
    try:
        chat = await event.get_chat()
        chname = (
            getattr(chat, "username", None)
            or getattr(chat, "title", "")
            or str(chat.id)
        )
        
        # Filter: only configured targets if WATCH set
        if WATCH:
            watch_ids = await resolve_watch()
            username = getattr(chat, "username", None)
            
            if username and f"@{username}" in WATCH:
                pass  # Allow
            elif chat.id in watch_ids:
                pass  # Allow
            else:
                return  # Skip
        
        doc = to_doc(event.message, chname)
        await produce(doc)
        
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
    except Exception as e:
        with OUT_LOG.open("a") as f:
            f.write(json.dumps({"error": str(e)}) + "\n")


@client.on(events.MessageEdited)
async def edited(event):
    """Handle message edits."""
    try:
        chat = await event.get_chat()
        chname = (
            getattr(chat, "username", None)
            or getattr(chat, "title", "")
            or str(chat.id)
        )
        
        doc = to_doc(event.message, chname)
        doc["edited"] = True
        await produce(doc)
        
    except Exception as e:
        with OUT_LOG.open("a") as f:
            f.write(json.dumps({"error": str(e)}) + "\n")


async def main():
    """Main entry point."""
    print("[telethon] Starting listener...")
    
    if not API_ID or not API_HASH:
        raise RuntimeError("TG_API_ID and TG_API_HASH required")
    
    # Connect
    if not client.is_connected():
        await client.connect()
    
    # Authorize (if needed)
    if not await client.is_user_authorized():
        if not PHONE:
            raise RuntimeError("TG_PHONE required for first login")
        
        await client.send_code_request(PHONE)
        code = input("Enter Telegram code: ")
        
        try:
            await client.sign_in(PHONE, code)
        except PhoneCodeInvalidError:
            raise SystemExit("Invalid code.")
    
    # Print watch list
    watch_ids = await resolve_watch()
    print(f"[telethon] Watching {len(watch_ids)} chats")
    print(f"[telethon] Listening... (log: {OUT_LOG})")
    
    # Run until disconnected
    await client.run_until_disconnected()


def shutdown(*args):
    """Shutdown handler."""
    try:
        client.disconnect()
    finally:
        print("[telethon] Stopped")


if __name__ == "__main__":
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(
            sig, lambda *_: asyncio.get_event_loop().create_task(client.disconnect())
        )
    
    asyncio.run(main())


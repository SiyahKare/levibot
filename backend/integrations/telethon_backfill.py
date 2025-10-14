"""
Telethon Backfill - Fetch historical messages
Usage: python telethon_backfill.py @groupname 2000
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

from telethon import TelegramClient

# Configuration
API_ID = int(os.getenv("TG_API_ID", "0"))
API_HASH = os.getenv("TG_API_HASH", "")
SESSION = os.getenv("TG_SESSION_NAME", "levibot_user")

# Paths
SESS_DIR = Path("backend/data/telethon_session")
OUT = Path("backend/data/logs/telethon/backfill.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)


async def run(username: str, limit: int = 2000):
    """
    Fetch historical messages from a group.
    
    Args:
        username: Group username (e.g., @groupname)
        limit: Maximum number of messages to fetch
    """
    async with TelegramClient(str(SESS_DIR / SESSION), API_ID, API_HASH) as client:
        print(f"[backfill] Fetching {limit} messages from {username}...")
        
        entity = await client.get_entity(username)
        count = 0
        
        async for msg in client.iter_messages(entity, limit=limit, reverse=True):
            doc = {
                "id": msg.id,
                "chat": username,
                "chat_id": getattr(entity, "id", None),
                "date": msg.date.isoformat() if msg.date else None,
                "text": msg.message or "",
                "media": bool(msg.media),
                "from_id": (
                    getattr(msg.from_id, "user_id", None)
                    if hasattr(msg, "from_id")
                    else None
                ),
            }
            
            with OUT.open("a", encoding="utf-8") as f:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            
            count += 1
            
            # Rate limit
            if count % 500 == 0:
                print(f"[backfill] Fetched {count} messages...")
                time.sleep(0.3)
        
        print(f"[backfill] Done! Fetched {count} messages to {OUT}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python telethon_backfill.py @groupname [limit]")
        sys.exit(1)
    
    username = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    
    asyncio.run(run(username, limit))


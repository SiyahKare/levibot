# lightweight in-proc pub/sub for events
from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self._subs: dict[int, asyncio.Queue[str]] = {}
        self._sid = 0
        self._lock = asyncio.Lock()

    async def subscribe(self) -> tuple[int, AsyncIterator[str]]:
        q: asyncio.Queue[str] = asyncio.Queue(maxsize=2048)
        async with self._lock:
            self._sid += 1
            sid = self._sid
            self._subs[sid] = q

        async def gen():
            try:
                while True:
                    yield await q.get()
            finally:
                async with self._lock:
                    self._subs.pop(sid, None)

        return sid, gen()

    async def publish(self, event: dict[str, Any]) -> None:
        msg = json.dumps(event, ensure_ascii=False)
        # non-blocking fanout; drop when queue full
        for q in list(self._subs.values()):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                # best-effort; drop message
                pass


BUS = EventBus()

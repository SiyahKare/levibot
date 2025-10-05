from __future__ import annotations
import asyncio, time, random, json
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable
import aiohttp

from ..infra.metrics import (
    alerts_enqueued_total, alerts_sent_total, alerts_failed_total,
    alerts_retry_total, alerts_queue_size_gauge,
)

@dataclass
class QueueConfig:
    rate_limit_per_sec: float = 1.0
    timeout_sec: float = 5.0
    max_retries: int = 3
    backoff_base: float = 0.8
    backoff_max: float = 8.0
    jitter: float = 0.2  # 0..1 oranında

class WebhookQueue:
    def __init__(self, cfg: QueueConfig, session_factory: Callable[[], aiohttp.ClientSession] = None):
        self.cfg = cfg
        self.q: asyncio.Queue[Dict[str, Any]] = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._closing = False
        self._next_available: Dict[str, float] = {}  # per-target RL
        self._session_factory = session_factory or (lambda: aiohttp.ClientSession())

    async def start(self):
        self._closing = False
        self._task = asyncio.create_task(self._run(), name="alerts-webhook-worker")

    async def stop(self):
        self._closing = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    def enqueue(self, target_url: str, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None, target_key: Optional[str] = None):
        item = {"url": target_url, "payload": payload, "headers": headers or {}, "target": target_key or target_url}
        self.q.put_nowait(item)
        alerts_enqueued_total.labels(target=item["target"]).inc()
        alerts_queue_size_gauge.set(self.q.qsize())

    async def _rate_limit_wait(self, key: str):
        now = time.time()
        nxt = self._next_available.get(key, now)
        delay = max(0.0, nxt - now)
        if delay > 0:
            await asyncio.sleep(delay)
        # next token time
        period = 1.0 / max(self.cfg.rate_limit_per_sec, 1e-6)
        self._next_available[key] = time.time() + period

    async def _send_once(self, session: aiohttp.ClientSession, url: str, payload: Dict[str, Any], headers: Dict[str, str]) -> int:
        async with session.post(url, json=payload, timeout=self.cfg.timeout_sec, headers=headers) as resp:
            # most webhooks return 2xx on success
            await resp.text()  # drain
            return resp.status

    async def _run(self):
        session = self._session_factory()
        try:
            while not self._closing:
                item = await self.q.get()
                alerts_queue_size_gauge.set(self.q.qsize())
                url, payload, headers, key = item["url"], item["payload"], item["headers"], item["target"]
                await self._rate_limit_wait(key)

                status = None
                ok = False
                for attempt in range(self.cfg.max_retries + 1):
                    try:
                        status = await self._send_once(session, url, payload, headers)
                        if 200 <= (status or 0) < 300:
                            ok = True
                            alerts_sent_total.labels(target=key, status=str(status)).inc()
                            break
                        else:
                            alerts_retry_total.labels(target=key, status=str(status)).inc()
                            # fallthrough to backoff
                    except Exception:
                        alerts_retry_total.labels(target=key, status="exc").inc()

                    # backoff
                    if attempt < self.cfg.max_retries:
                        base = min(self.cfg.backoff_max, self.cfg.backoff_base * (2 ** attempt))
                        jitter = 1.0 + (random.uniform(-self.cfg.jitter, self.cfg.jitter))
                        await asyncio.sleep(max(0.05, base * jitter))
                if not ok:
                    alerts_failed_total.labels(target=key, status=str(status or "exc")).inc()
                self.q.task_done()
        finally:
            await session.close()

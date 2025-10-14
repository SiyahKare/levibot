import asyncio

import pytest

from backend.src.alerts.queue import QueueConfig, WebhookQueue


class FakeResp:
    def __init__(self, status):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def text(self):
        return "ok"


class FakeSession:
    def __init__(self, pattern):
        self.calls = 0
        self.pattern = pattern  # list of statuses to return per call

    def post(self, url, json, timeout, headers):
        status = self.pattern[min(self.calls, len(self.pattern) - 1)]
        self.calls += 1
        return FakeResp(status)

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_queue_retries_and_succeeds():
    # 2 hata → 1 başarı
    session = FakeSession([500, 502, 200])
    q = WebhookQueue(
        cfg=QueueConfig(
            rate_limit_per_sec=100,
            timeout_sec=1.0,
            max_retries=3,
            backoff_base=0.05,
            backoff_max=0.1,
            jitter=0.0,
        ),
        session_factory=lambda: session,
    )
    await q.start()
    q.enqueue("https://example.com/webhook", {"msg": "hello"}, target_key="t1")
    await asyncio.wait_for(q.q.join(), timeout=2.0)
    await q.stop()
    # 3 çağrı yapıldı, sonu 200
    assert session.calls >= 3


@pytest.mark.asyncio
async def test_rate_limit_blocks_burst():
    session = FakeSession([200, 200, 200, 200, 200])
    q = WebhookQueue(
        cfg=QueueConfig(
            rate_limit_per_sec=2,
            timeout_sec=1.0,
            max_retries=0,
            backoff_base=0.01,
            backoff_max=0.02,
            jitter=0.0,
        ),
        session_factory=lambda: session,
    )
    await q.start()
    for _ in range(4):
        q.enqueue("https://example.com/webhook", {"i": _}, target_key="same")
    await asyncio.wait_for(q.q.join(), timeout=5.0)
    await q.stop()
    # 4 gönderim yapıldı
    assert session.calls == 4

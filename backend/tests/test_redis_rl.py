import os, pytest, asyncio
from backend.src.infra import redis_rl

def test_fallback_allow():
    # Redis URL yoksa fallback mode
    original = os.environ.get("REDIS_URL")
    if "REDIS_URL" in os.environ:
        del os.environ["REDIS_URL"]
    try:
        assert redis_rl.enabled() is False
        ok, cnt, reset_at = asyncio.run(redis_rl.check_allow("test:fallback"))
        assert ok is True and cnt >= 1 and reset_at > 0
    finally:
        if original:
            os.environ["REDIS_URL"] = original

def test_redis_path_if_available():
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("no redis in CI (set REDIS_URL to test)")
    assert redis_rl.enabled() is True
    # İki ardışık çağrı → count artmalı
    ok1, cnt1, _ = asyncio.run(redis_rl.check_allow("test:bucket:seq"))
    ok2, cnt2, _ = asyncio.run(redis_rl.check_allow("test:bucket:seq"))
    assert cnt2 == cnt1 + 1

def test_redis_rate_limit_enforcement():
    url = os.getenv("REDIS_URL")
    if not url:
        pytest.skip("no redis in CI")
    # Küçük limit ile test
    os.environ["RL_MAX"] = "3"
    os.environ["RL_BURST"] = "1"
    os.environ["RL_WINDOW_SEC"] = "60"
    
    bucket = "test:enforce:limit"
    results = []
    for i in range(6):
        ok, cnt, reset_at = asyncio.run(redis_rl.check_allow(bucket))
        results.append(ok)
    
    # İlk 4 (3+1 burst) geçmeli, sonrası block
    assert results[:4].count(True) == 4
    assert results[4:].count(False) >= 1

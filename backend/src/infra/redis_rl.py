from __future__ import annotations

import os
import time

try:
    import redis.asyncio as redis
except Exception:
    redis = None

def enabled() -> bool:
    return bool(os.getenv("REDIS_URL")) and redis is not None

def _cfg():
    return {
        "window": int(os.getenv("RL_WINDOW_SEC", "60")),
        "max": int(os.getenv("RL_MAX", "120")),
        "burst": int(os.getenv("RL_BURST", "40")),
    }

async def get_client():
    assert enabled(), "redis rl not enabled"
    return redis.from_url(os.getenv("REDIS_URL"), encoding="utf-8", decode_responses=True)

# token-bucket benzeri: (count, reset_at)
LUA_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max = tonumber(ARGV[3])
local burst = tonumber(ARGV[4])
local slot = math.floor(now / window)
local k = key .. ":" .. slot
local cnt = redis.call("INCR", k)
if cnt == 1 then
  redis.call("EXPIRE", k, window)
end
local allowed = 0
if cnt <= (max + burst) then
  allowed = 1
end
local reset_at = (slot + 1) * window
return {allowed, cnt, reset_at}
"""

async def check_allow(bucket_key: str) -> tuple[bool, int, int]:
    """
    Redis-backed token bucket rate limiter.
    Returns: (allowed, count, reset_at)
    """
    if not enabled():
        # fallback: in-memory gibi davranan gevşek allow
        now = int(time.time())
        return True, 1, now + _cfg()["window"]
    cfg = _cfg()
    try:
        cli = await get_client()
        res = await cli.eval(
            LUA_SCRIPT,
            1,
            bucket_key,
            int(time.time()),
            cfg["window"],
            cfg["max"],
            cfg["burst"],
        )
        allowed = int(res[0]) == 1
        cnt = int(res[1])
        reset_at = int(res[2])
        await cli.close()
        return allowed, cnt, reset_at
    except Exception:
        now = int(time.time())
        return True, 1, now + cfg["window"]

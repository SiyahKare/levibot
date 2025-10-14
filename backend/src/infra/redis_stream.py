"""
Redis Streams for Realtime Data Pipeline
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from .settings import settings

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis | None:
    """Get or create Redis client."""
    global _redis_client
    
    if not settings.REDIS_URL:
        return None
    
    if redis is None:
        raise ImportError("redis not installed. Run: pip install redis")
    
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    
    return _redis_client


async def set_last_tick(symbol: str, tick_dict: dict[str, Any]) -> None:
    """
    Store latest tick price in Redis hash + push to stream.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
        tick_dict: Tick data dictionary
    """
    r = await get_redis()
    if not r:
        return
    
    try:
        # Store as hash for instant lookups
        await r.hset(
            f"last:{symbol}",
            mapping={k: str(v) for k, v in tick_dict.items()},
        )
        
        # Push to stream for consumers
        await r.xadd(
            settings.STREAM_TOPIC_TICKS,
            {"symbol": symbol, "tick": json.dumps(tick_dict)},
            maxlen=settings.STREAM_MAXLEN,
            approximate=True,
        )
    except Exception as e:
        print(f"[Redis] Error setting tick for {symbol}: {e}")


async def get_last_tick(symbol: str) -> dict[str, Any] | None:
    """Get latest tick from Redis hash."""
    r = await get_redis()
    if not r:
        return None
    
    try:
        data = await r.hgetall(f"last:{symbol}")
        if not data:
            return None
        
        # Convert string values back to numbers where applicable
        result = {}
        for k, v in data.items():
            if v.replace(".", "", 1).replace("-", "", 1).isdigit():
                result[k] = float(v)
            else:
                result[k] = v
        
        return result
    except Exception as e:
        print(f"[Redis] Error getting tick for {symbol}: {e}")
        return None


async def publish_signal(signal_dict: dict[str, Any]) -> None:
    """Publish trading signal to Redis stream."""
    r = await get_redis()
    if not r:
        return
    
    try:
        await r.xadd(
            settings.STREAM_TOPIC_SIGNALS,
            {"signal": json.dumps(signal_dict)},
            maxlen=settings.STREAM_MAXLEN,
            approximate=True,
        )
    except Exception as e:
        print(f"[Redis] Error publishing signal: {e}")


async def publish_event(event_dict: dict[str, Any]) -> None:
    """Publish event to Redis stream."""
    r = await get_redis()
    if not r:
        return
    
    try:
        await r.xadd(
            settings.STREAM_TOPIC_EVENTS,
            {"event": json.dumps(event_dict)},
            maxlen=settings.STREAM_MAXLEN,
            approximate=True,
        )
    except Exception as e:
        print(f"[Redis] Error publishing event: {e}")


async def consume_stream(
    stream_key: str,
    callback,
    batch_size: int = 100,
    block_ms: int = 1000,
) -> None:
    """
    Consume messages from Redis stream.
    
    Args:
        stream_key: Stream name (e.g., "ticks", "signals")
        callback: Async function to process each message
        batch_size: Max messages per read
        block_ms: Block timeout in milliseconds
    """
    r = await get_redis()
    if not r:
        return
    
    last_id = "0-0"
    
    while True:
        try:
            streams = await r.xread(
                {stream_key: last_id},
                block=block_ms,
                count=batch_size,
            )
            
            if not streams:
                continue
            
            for stream_name, entries in streams:
                for entry_id, data in entries:
                    last_id = entry_id
                    await callback(data)
        
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Redis] Error consuming stream {stream_key}: {e}")
            await asyncio.sleep(1)


async def close_redis() -> None:
    """Close Redis connection gracefully."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None








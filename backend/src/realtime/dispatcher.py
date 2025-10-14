"""
Realtime Dispatcher - Central Event Processing Pipeline

Consumes events from Redis streams and routes them to appropriate handlers.
"""
from __future__ import annotations

import asyncio
import json

from ..infra.redis_stream import consume_stream, get_redis
from ..infra.settings import settings
from ..trading.paper_engine_rt import RealtimePaperEngine

# Global engine instance
engine = RealtimePaperEngine()


async def handle_tick(data: dict[str, str]) -> None:
    """Process tick update from Redis stream."""
    try:
        tick_json = data.get("tick")
        if not tick_json:
            return
        
        tick = json.loads(tick_json)
        await engine.on_tick(tick)
    except Exception as e:
        print(f"[Dispatcher] Error handling tick: {e}")


async def handle_signal(data: dict[str, str]) -> None:
    """Process trading signal from Redis stream."""
    try:
        signal_json = data.get("signal")
        if not signal_json:
            return
        
        signal = json.loads(signal_json)
        await engine.execute_signal(signal)
    except Exception as e:
        print(f"[Dispatcher] Error handling signal: {e}")


async def run_dispatcher() -> None:
    """
    Run the main dispatcher loop.
    
    Consumes from multiple Redis streams:
    - ticks: Market price updates → PnL calculation
    - signals: Trading signals → Order execution
    """
    print("[Dispatcher] Starting...")
    
    # Ensure Redis is available
    r = await get_redis()
    if not r:
        print("[Dispatcher] ERROR: Redis not configured. Set REDIS_URL environment variable.")
        return
    
    print(f"[Dispatcher] Connected to Redis: {settings.REDIS_URL}")
    print(f"[Dispatcher] Consuming streams: {settings.STREAM_TOPIC_TICKS}, {settings.STREAM_TOPIC_SIGNALS}")
    
    # Start consumers in parallel
    await asyncio.gather(
        consume_stream(settings.STREAM_TOPIC_TICKS, handle_tick, batch_size=500, block_ms=1000),
        consume_stream(settings.STREAM_TOPIC_SIGNALS, handle_signal, batch_size=100, block_ms=1000),
    )


if __name__ == "__main__":
    asyncio.run(run_dispatcher())








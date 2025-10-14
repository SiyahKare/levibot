"""
MEXC WebSocket Real-time Feed

Connects to MEXC WebSocket API and streams live market data to Redis.
"""
from __future__ import annotations

import asyncio
import json
import time

try:
    import websockets
except ImportError:
    websockets = None

from ..infra.db import write_ticks_batch
from ..infra.redis_stream import set_last_tick
from ..infra.settings import settings
from ..realtime.schemas import Tick
from .normalize import denorm_symbol, norm_symbol

# MEXC WebSocket URLs
MEXC_WS_URL = "wss://wbs.mexc.com/ws"
MEXC_WS_URL_SPOT = "wss://wbs.mexc.com/raw/ws"  # Alternative spot endpoint


class MexcWebSocketFeed:
    """
    MEXC WebSocket client with auto-reconnect and batching.
    
    Features:
    - Real-time ticker updates
    - Automatic reconnection
    - Batch writes to TimescaleDB
    - Publish to Redis streams
    """
    
    def __init__(self, symbols: list[str]):
        self.symbols = symbols
        self.batch: list[tuple] = []
        self.last_flush = time.time()
        self.running = False
    
    async def connect_and_stream(self) -> None:
        """Main connection loop with auto-reconnect."""
        if websockets is None:
            raise ImportError("websockets not installed. Run: pip install websockets")
        
        while self.running:
            try:
                async with websockets.connect(
                    MEXC_WS_URL,
                    ping_interval=settings.WS_PING_INTERVAL,
                    ping_timeout=10,
                ) as ws:
                    print(f"[MEXC WS] Connected. Subscribing to {len(self.symbols)} symbols...")
                    
                    # Subscribe to ticker channels
                    for symbol in self.symbols:
                        mexc_symbol = denorm_symbol(symbol, "mexc")
                        # Subscribe to ticker updates (best bid/ask + last trade)
                        sub_msg = {
                            "method": "SUBSCRIPTION",
                            "params": [
                                f"spot@public.bookTicker.v3.api@{mexc_symbol}",
                                f"spot@public.deals.v3.api@{mexc_symbol}",
                            ],
                        }
                        await ws.send(json.dumps(sub_msg))
                        print(f"[MEXC WS] Subscribed to {mexc_symbol}")
                    
                    # Message processing loop
                    async for raw_msg in ws:
                        try:
                            await self._process_message(raw_msg)
                        except Exception as e:
                            print(f"[MEXC WS] Error processing message: {e}")
                            continue
            
            except Exception as e:
                print(f"[MEXC WS] Connection error: {e}")
                print(f"[MEXC WS] Reconnecting in {settings.WS_RECONNECT_SECS}s...")
                await asyncio.sleep(settings.WS_RECONNECT_SECS)
    
    async def _process_message(self, raw_msg: str) -> None:
        """Parse and process WebSocket message."""
        try:
            msg = json.loads(raw_msg)
        except json.JSONDecodeError:
            return
        
        # Skip non-data messages (ping/pong, subscriptions, etc.)
        if not isinstance(msg, dict):
            return
        
        # Extract channel info
        channel = msg.get("c", "")
        data = msg.get("d", {})
        
        if not channel or not data:
            return
        
        # Parse different message types
        symbol = self._extract_symbol(channel)
        if not symbol:
            return
        
        normalized_symbol = norm_symbol(symbol, "mexc")
        ts = time.time()
        
        # Book ticker update (bid/ask)
        if "bookTicker" in channel:
            tick = Tick(
                ts=ts,
                venue="mexc",
                symbol=normalized_symbol,
                last=float(data.get("p", 0)),
                bid=float(data.get("b", 0)),
                ask=float(data.get("a", 0)),
            )
            await self._handle_tick(tick)
        
        # Deal update (last trade)
        elif "deals" in channel:
            tick = Tick(
                ts=ts,
                venue="mexc",
                symbol=normalized_symbol,
                last=float(data.get("p", 0)),
                volume=float(data.get("v", 0)),
            )
            await self._handle_tick(tick)
    
    def _extract_symbol(self, channel: str) -> str | None:
        """Extract symbol from channel name."""
        # Example: "spot@public.bookTicker.v3.api@btcusdt" -> "btcusdt"
        parts = channel.split("@")
        if len(parts) >= 3:
            return parts[-1]
        return None
    
    async def _handle_tick(self, tick: Tick) -> None:
        """Process tick: update Redis, batch for DB."""
        # Update Redis with latest price
        await set_last_tick(tick.symbol, tick.model_dump())
        
        # Add to batch for TimescaleDB
        self.batch.append((
            tick.ts,
            tick.venue,
            tick.symbol,
            tick.last,
            tick.bid,
            tick.ask,
            tick.mark,
            tick.volume,
            "ws",
        ))
        
        # Flush batch if needed
        now = time.time()
        should_flush = (
            len(self.batch) >= settings.DB_BATCH_SIZE
            or (now - self.last_flush) >= settings.DB_FLUSH_INTERVAL_SEC
        )
        
        if should_flush:
            await self._flush_batch()
    
    async def _flush_batch(self) -> None:
        """Write batch to TimescaleDB."""
        if not self.batch:
            return
        
        try:
            await write_ticks_batch(self.batch)
            self.batch = []
            self.last_flush = time.time()
        except Exception as e:
            print(f"[MEXC WS] Error flushing batch: {e}")
    
    async def start(self) -> None:
        """Start WebSocket feed."""
        self.running = True
        await self.connect_and_stream()
    
    async def stop(self) -> None:
        """Stop WebSocket feed gracefully."""
        self.running = False
        await self._flush_batch()  # Flush remaining data


async def run_mexc_feed(symbols: list[str] | None = None) -> None:
    """
    Run MEXC WebSocket feed indefinitely.
    
    Args:
        symbols: List of symbols to stream. Defaults to settings.SYMBOLS
    """
    if symbols is None:
        symbols = settings.SYMBOLS
    
    feed = MexcWebSocketFeed(symbols)
    await feed.start()


if __name__ == "__main__":
    # Standalone runner
    asyncio.run(run_mexc_feed())








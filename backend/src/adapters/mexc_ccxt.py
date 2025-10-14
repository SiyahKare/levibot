"""MEXC exchange adapter using ccxt for REST and ccxt.pro for WebSocket."""

import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator

import ccxt
import ccxt.pro as ccxtpro


class MexcAdapter:
    """MEXC exchange adapter using ccxt for REST and ccxt.pro for WebSocket."""

    def __init__(self, symbols: list[str], rate_limit: bool = True):
        self.rest = ccxt.mexc({"enableRateLimit": rate_limit})
        self.ws = ccxtpro.mexc()
        self.symbols = symbols

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1m", limit: int = 1500
    ) -> list[list]:
        """Fetch OHLCV bars via REST API."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.rest.fetch_ohlcv, symbol, timeframe, None, limit
        )

    async def fetch_orderbook(self, symbol: str, limit: int = 50) -> dict[str, Any]:
        """Fetch orderbook snapshot via REST API."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.rest.fetch_order_book, symbol, limit
        )

    async def stream_trades(self, symbol: str) -> AsyncIterator[dict[str, Any]]:
        """Stream trades via WebSocket with auto-reconnect."""
        while True:
            try:
                trades = await self.ws.watch_trades(symbol)
                for t in trades:
                    yield {
                        "ts": int(t["timestamp"]),
                        "price": float(t["price"]),
                        "amount": float(t["amount"]),
                        "side": t.get("side", ""),
                    }
            except Exception:
                await asyncio.sleep(1.0)  # reconnect/backoff

    async def stream_ticker(self, symbol: str) -> AsyncIterator[dict[str, Any]]:
        """Stream ticker via WebSocket with auto-reconnect."""
        while True:
            try:
                tk = await self.ws.watch_ticker(symbol)
                yield {
                    "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "bid": float(tk.get("bid", 0) or 0),
                    "ask": float(tk.get("ask", 0) or 0),
                    "last": float(tk.get("last", 0) or 0),
                    "spread": float(tk.get("ask", 0) or 0)
                    - float(tk.get("bid", 0) or 0),
                    "volume": float(tk.get("baseVolume", 0) or 0),
                }
            except Exception:
                await asyncio.sleep(1.0)

    async def close(self):
        """Close WebSocket connection."""
        await self.ws.close()


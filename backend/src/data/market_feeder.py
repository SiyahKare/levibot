"""Market data feeder that streams live data to trading engines."""

import asyncio
from collections.abc import Callable
from typing import Any

from ..adapters.mexc_ccxt import MexcAdapter
from .gap_filler import fill_minute_bars


class MarketFeeder:
    """Feeds market data to trading engines via callback."""

    def __init__(self, symbols: list[str], adapter: MexcAdapter | None = None):
        self.symbols = symbols
        self.adapter = adapter or MexcAdapter(symbols)

    async def bootstrap_bars(self, symbol: str) -> list[list]:
        """Fetch and gap-fill initial OHLCV bars."""
        raw = await self.adapter.fetch_ohlcv(symbol, "1m", 1500)
        return fill_minute_bars(sorted(raw, key=lambda r: r[0]))

    async def stream_symbol(self, symbol: str, on_md: Callable[[dict[str, Any]], None]):
        """Stream market data for a single symbol using REST API polling."""
        # Bootstrap with historical bars
        bars = await self.bootstrap_bars(symbol)
        last = bars[-1][4] if bars else 0.0

        async def run_ticker():
            """Poll ticker data every 5 seconds using REST API."""
            nonlocal last  # Use the last variable from outer scope
            while True:
                try:
                    # Use REST API instead of WebSocket
                    ticker = await self.adapter.fetch_ticker(symbol)

                    md = {
                        "symbol": symbol,
                        "price": ticker.get("last", last),
                        "spread": ticker.get("ask", 0) - ticker.get("bid", 0),
                        "vol": ticker.get("baseVolume", 0),
                        "texts": [],  # Placeholder for news/tweets
                        "funding": 0.0,  # Placeholder for funding rate
                        "oi": 0.0,  # Placeholder for open interest
                    }
                    await on_md(md)

                    # Update last price
                    last = md["price"]

                except Exception as e:
                    print(f"❌ Error fetching ticker for {symbol}: {e}")

                # Poll every 5 seconds
                await asyncio.sleep(5.0)

        await run_ticker()

    async def run(self, on_md: Callable[[dict[str, Any]], None]):
        """Run market data streams for all symbols."""
        await asyncio.gather(*(self.stream_symbol(s, on_md) for s in self.symbols))

    async def close(self):
        """Close adapter connections."""
        await self.adapter.close()

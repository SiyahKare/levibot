"""Market data feeder that streams live data to trading engines."""

import asyncio
from typing import Any, Callable, Optional

from ..adapters.mexc_ccxt import MexcAdapter
from .gap_filler import fill_minute_bars


class MarketFeeder:
    """Feeds market data to trading engines via callback."""

    def __init__(self, symbols: list[str], adapter: Optional[MexcAdapter] = None):
        self.symbols = symbols
        self.adapter = adapter or MexcAdapter(symbols)

    async def bootstrap_bars(self, symbol: str) -> list[list]:
        """Fetch and gap-fill initial OHLCV bars."""
        raw = await self.adapter.fetch_ohlcv(symbol, "1m", 1500)
        return fill_minute_bars(sorted(raw, key=lambda r: r[0]))

    async def stream_symbol(
        self, symbol: str, on_md: Callable[[dict[str, Any]], None]
    ):
        """Stream market data for a single symbol."""
        # Bootstrap with historical bars
        bars = await self.bootstrap_bars(symbol)
        last = bars[-1][4] if bars else 0.0

        async def run_ticker():
            async for tk in self.adapter.stream_ticker(symbol):
                md = {
                    "symbol": symbol,
                    "price": tk["last"] or last,
                    "spread": tk["spread"],
                    "vol": tk["volume"],
                    "texts": [],  # Placeholder for news/tweets
                    "funding": 0.0,  # Placeholder for funding rate
                    "oi": 0.0,  # Placeholder for open interest
                }
                await on_md(md)

        async def run_trades():
            async for tr in self.adapter.stream_trades(symbol):
                pass  # Optional: aggregate trade-based volume/OI

        await asyncio.gather(run_ticker(), run_trades())

    async def run(self, on_md: Callable[[dict[str, Any]], None]):
        """Run market data streams for all symbols."""
        await asyncio.gather(*(self.stream_symbol(s, on_md) for s in self.symbols))

    async def close(self):
        """Close adapter connections."""
        await self.adapter.close()


"""Tests for market feeder."""

import pytest

from src.adapters.mexc_ccxt import MexcAdapter
from src.data.market_feeder import MarketFeeder


class DummyAdapter(MexcAdapter):
    """Mock adapter for testing without network calls."""

    def __init__(self):
        pass  # Skip parent init

    async def fetch_ohlcv(self, symbol, timeframe="1m", limit=1500):
        base = 1_700_000_000_000
        return [
            [base, 1, 2, 0.5, 1.0, 10],
            [base + 3 * 60_000, 1, 2, 0.5, 1.1, 10],
        ]

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_bootstrap_fills_gaps():
    """Test that bootstrap fills gaps in OHLCV data."""
    feeder = MarketFeeder(["BTC/USDT"], adapter=DummyAdapter())
    bars = await feeder.bootstrap_bars("BTC/USDT")

    # Should have 4 bars: original 2 + 2 synthetic
    assert len(bars) == 4


@pytest.mark.asyncio
async def test_feeder_stores_symbols():
    """Test that feeder stores symbol list."""
    symbols = ["BTC/USDT", "ETH/USDT"]
    feeder = MarketFeeder(symbols, adapter=DummyAdapter())

    assert feeder.symbols == symbols


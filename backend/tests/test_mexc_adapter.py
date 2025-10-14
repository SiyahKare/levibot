"""Tests for MEXC adapter signatures (no network calls)."""

import pytest

from src.adapters.mexc_ccxt import MexcAdapter


@pytest.mark.asyncio
async def test_adapter_has_required_methods():
    """Verify adapter has required methods (no network calls)."""
    adapter = MexcAdapter(["BTC/USDT"])

    assert hasattr(adapter, "fetch_ohlcv")
    assert hasattr(adapter, "fetch_orderbook")
    assert hasattr(adapter, "stream_ticker")
    assert hasattr(adapter, "stream_trades")
    assert hasattr(adapter, "close")


def test_adapter_stores_symbols():
    """Test that adapter stores symbol list."""
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    adapter = MexcAdapter(symbols)

    assert adapter.symbols == symbols


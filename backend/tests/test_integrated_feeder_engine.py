"""Integration tests for MarketFeeder → Engine flow."""

import asyncio

import pytest

from src.engine.engine import TradingEngine
from src.engine.manager import EngineManager


@pytest.mark.asyncio
async def test_symbol_specific_md_flow():
    """Test that market data flows to correct engine via push_md."""
    config = {
        "engine_defaults": {"cycle_interval": 0.01, "md_queue_max": 4}
    }
    
    manager = EngineManager(config)
    await manager.start_engine("BTC/USDT")
    engine = manager.engines["BTC/USDT"]

    # Simulate feeder pushing MD directly to engine
    md = {
        "symbol": "BTC/USDT",
        "price": 42000.0,
        "spread": 0.1,
        "vol": 1000.0,
        "texts": [],
        "funding": 0.0,
        "oi": 0.0,
    }
    await engine.push_md(md)

    # Engine should retrieve the same MD
    got = await engine._get_md()
    assert got["symbol"] == "BTC/USDT"
    assert got["price"] == 42000.0
    assert got["spread"] == 0.1

    await manager.stop_all()


@pytest.mark.asyncio
async def test_md_queue_backpressure():
    """Test that queue drops oldest when full."""
    config = {
        "engine_defaults": {"cycle_interval": 0.01, "md_queue_max": 2}
    }
    
    manager = EngineManager(config)
    await manager.start_engine("ETH/USDT")
    engine = manager.engines["ETH/USDT"]

    # Fill queue beyond capacity
    await engine.push_md({"symbol": "ETH/USDT", "price": 1.0, "spread": 0.0, "vol": 0.0, "texts": []})
    await engine.push_md({"symbol": "ETH/USDT", "price": 2.0, "spread": 0.0, "vol": 0.0, "texts": []})
    await engine.push_md({"symbol": "ETH/USDT", "price": 3.0, "spread": 0.0, "vol": 0.0, "texts": []})

    # Queue should have only 2 items (oldest dropped)
    md1 = await engine._get_md()
    md2 = await engine._get_md()

    # Should get items 2 and 3 (item 1 was dropped)
    assert md1["price"] == 2.0
    assert md2["price"] == 3.0

    await manager.stop_all()


@pytest.mark.asyncio
async def test_md_timeout_returns_empty():
    """Test that _get_md returns empty dict on timeout."""
    config = {
        "engine_defaults": {"cycle_interval": 0.01, "md_queue_max": 4}
    }
    
    manager = EngineManager(config)
    await manager.start_engine("SOL/USDT")
    engine = manager.engines["SOL/USDT"]

    # Don't push any MD, should timeout
    md = await engine._get_md()
    
    assert md["price"] is None
    assert md["spread"] is None
    assert md["vol"] == 0.0

    await manager.stop_all()


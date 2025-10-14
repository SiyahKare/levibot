"""
Smoke tests for trading engine.
"""

import asyncio
import logging

import pytest
from src.engine.engine import EngineStatus, TradingEngine


@pytest.mark.asyncio
async def test_engine_lifecycle():
    """Test engine start/stop lifecycle."""
    config = {"cycle_interval": 0.05}
    logger = logging.getLogger("test")

    engine = TradingEngine("TESTUSDT", config, logger)

    # Initially stopped
    assert engine.status == EngineStatus.STOPPED

    # Start
    await engine.start()
    await asyncio.sleep(0.15)
    assert engine.status == EngineStatus.RUNNING

    # Stop
    await engine.stop()
    assert engine.status == EngineStatus.STOPPED


@pytest.mark.asyncio
async def test_engine_health():
    """Test health metrics."""
    config = {"cycle_interval": 0.05}
    logger = logging.getLogger("test")

    engine = TradingEngine("TESTUSDT", config, logger)
    await engine.start()
    await asyncio.sleep(0.5)

    health = engine.get_health()
    assert health["symbol"] == "TESTUSDT"
    assert health["status"] == "running"
    assert health["uptime_seconds"] > 0
    assert health["last_heartbeat"] is not None

    await engine.stop()


@pytest.mark.asyncio
async def test_multiple_engines():
    """Test multiple engines running concurrently."""
    logger = logging.getLogger("test")
    config = {"cycle_interval": 0.1}

    engines = [
        TradingEngine("BTC/USDT", config, logger),
        TradingEngine("ETH/USDT", config, logger),
        TradingEngine("SOL/USDT", config, logger),
    ]

    # Start all
    for engine in engines:
        await engine.start()

    await asyncio.sleep(0.5)

    # Check all running
    for engine in engines:
        assert engine.status == EngineStatus.RUNNING
        health = engine.get_health()
        assert health["uptime_seconds"] > 0

    # Stop all
    for engine in engines:
        await engine.stop()

    # Check all stopped
    for engine in engines:
        assert engine.status == EngineStatus.STOPPED

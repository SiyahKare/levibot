"""
Smoke tests for engine manager.
"""

import asyncio

import pytest
from src.engine.manager import EngineManager


@pytest.mark.asyncio
async def test_manager_multi_engine():
    """Test manager with multiple engines."""
    config = {"engine_defaults": {"cycle_interval": 0.05}}
    manager = EngineManager(config)

    await manager.start_all(["BTC/USDT", "ETH/USDT", "SOL/USDT"])

    await asyncio.sleep(0.3)

    summary = manager.get_summary()
    assert summary["total"] == 3
    assert summary["running"] == 3

    await manager.stop_all()


@pytest.mark.asyncio
async def test_manager_start_stop_single():
    """Test starting and stopping a single engine."""
    config = {"engine_defaults": {"cycle_interval": 0.05}}
    manager = EngineManager(config)

    # Start one engine
    await manager.start_engine("TEST/USDT")
    await asyncio.sleep(0.2)

    status = manager.get_engine_status("TEST/USDT")
    assert status is not None
    assert status["status"] == "running"

    # Stop it
    await manager.stop_engine("TEST/USDT")

    status = manager.get_engine_status("TEST/USDT")
    assert status is None

    await manager.stop_all()


@pytest.mark.asyncio
async def test_manager_restart():
    """Test engine restart."""
    config = {"engine_defaults": {"cycle_interval": 0.05}}
    manager = EngineManager(config)

    await manager.start_engine("TEST/USDT")
    await asyncio.sleep(0.2)

    # Restart
    await manager.restart_engine("TEST/USDT")
    await asyncio.sleep(0.2)

    status = manager.get_engine_status("TEST/USDT")
    assert status is not None
    assert status["status"] == "running"

    await manager.stop_all()

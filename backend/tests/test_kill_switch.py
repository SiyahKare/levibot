"""Test kill switch functionality."""

import pytest

from src.exchange.executor import OrderExecutor


class DummyRisk:
    """Mock RiskManager for testing."""

    def __init__(self, global_stop: bool = False):
        self._global_stop = global_stop

    def is_global_stop(self):
        return self._global_stop

    def can_open_new_position(self, symbol: str):
        return True


class DummyBroker:
    """Mock MexcOrders for testing."""

    async def place_order(self, *args, **kwargs):
        return {"ok": True, "orderId": "test123"}


class DummyPortfolio:
    """Mock Portfolio for testing."""

    def exposure_notional(self, symbol: str, price: float):
        return 0.0


@pytest.mark.asyncio
async def test_manual_kill_switch_blocks_orders():
    """Test that manual kill switch blocks order execution."""
    executor = OrderExecutor(
        DummyRisk(),
        DummyBroker(),
        DummyPortfolio(),
        kill_threshold_usd=0,
    )

    # Engage kill switch manually
    executor.engage_kill_switch("manual")

    # Try to execute order
    result = await executor.execute_signal("BTC/USDT", "BUY", 0.01, 100.0)

    # Should be blocked
    assert result["ok"] is False
    assert result["reason"] == "kill_switch"


@pytest.mark.asyncio
async def test_auto_kill_on_global_stop():
    """Test that global stop triggers automatic kill switch."""
    risk = DummyRisk(global_stop=True)
    executor = OrderExecutor(
        risk, DummyBroker(), DummyPortfolio(), kill_threshold_usd=0
    )

    # Try to execute order with global stop active
    result = await executor.execute_signal("BTC/USDT", "BUY", 0.01, 100.0)

    # Should be blocked and kill switch should be engaged
    assert result["ok"] is False
    assert result["reason"] == "kill_switch"
    assert executor.kill_on is True


@pytest.mark.asyncio
async def test_exposure_limit_triggers_kill():
    """Test that exposure limit triggers kill switch."""

    class HighExposurePortfolio:
        def exposure_notional(self, symbol: str, price: float):
            return 3000.0  # Above threshold

    executor = OrderExecutor(
        DummyRisk(),
        DummyBroker(),
        HighExposurePortfolio(),
        kill_threshold_usd=2000,  # 2k limit
    )

    # Try to execute order
    result = await executor.execute_signal("BTC/USDT", "BUY", 0.01, 100.0)

    # Should trigger kill switch due to exposure
    assert result["ok"] is False
    assert result["reason"] == "exposure_limit"
    assert executor.kill_on is True


@pytest.mark.asyncio
async def test_risk_block_prevents_execution():
    """Test that risk manager block prevents execution."""

    class BlockingRisk:
        def is_global_stop(self):
            return False

        def can_open_new_position(self, symbol: str):
            return False  # Block all orders

    executor = OrderExecutor(
        BlockingRisk(), DummyBroker(), DummyPortfolio(), kill_threshold_usd=0
    )

    result = await executor.execute_signal("BTC/USDT", "BUY", 0.01, 100.0)

    # Should be blocked by risk manager
    assert result["ok"] is False
    assert result["reason"] == "risk_block"


@pytest.mark.asyncio
async def test_successful_execution():
    """Test successful order execution when all checks pass."""
    executor = OrderExecutor(
        DummyRisk(), DummyBroker(), DummyPortfolio(), kill_threshold_usd=0
    )

    result = await executor.execute_signal("BTC/USDT", "BUY", 0.01, 100.0)

    # Should succeed
    assert result["ok"] is True
    assert "orderId" in result


"""Test order idempotency via clientOrderId."""

import pytest

from src.exchange.mexc_orders import MexcOrders


@pytest.mark.asyncio
async def test_idempotent_id_stable():
    """Test that same order params generate same clientOrderId."""
    broker = MexcOrders("test_key", "test_secret", "https://testnet.mexc.com")

    # Place order twice with same params
    order1 = await broker.place_order("BTC/USDT", "BUY", 0.01)
    order2 = await broker.place_order(
        "BTC/USDT", "BUY", 0.01, client_order_id=order1["orderId"]
    )

    # Should have same orderId (idempotent)
    assert order1["orderId"] == order2["orderId"]
    assert order1["ok"] is True
    assert order2["ok"] is True


@pytest.mark.asyncio
async def test_different_params_different_id():
    """Test that different params generate different clientOrderId."""
    broker = MexcOrders("test_key", "test_secret", "https://testnet.mexc.com")

    order1 = await broker.place_order("BTC/USDT", "BUY", 0.01)
    order2 = await broker.place_order("BTC/USDT", "BUY", 0.02)  # Different qty

    # Should have different orderIds
    assert order1["orderId"] != order2["orderId"]


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test that rate limiting enforces min delay between requests."""
    import time

    broker = MexcOrders("test_key", "test_secret", "https://testnet.mexc.com", rate_limit_rps=10)

    start = time.time()
    await broker.place_order("BTC/USDT", "BUY", 0.01)
    await broker.place_order("BTC/USDT", "BUY", 0.01)
    elapsed = time.time() - start

    # Should take at least 0.1s (1/10 rps)
    assert elapsed >= 0.1


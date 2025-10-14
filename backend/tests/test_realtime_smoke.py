"""
Realtime System Smoke Tests

Quick validation of core realtime components.
"""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_redis_stream_publish():
    """Test Redis stream publish functionality."""
    from backend.src.infra.redis_stream import get_redis, set_last_tick
    
    r = await get_redis()
    if not r:
        pytest.skip("Redis not configured")
    
    # Publish a test tick
    tick = {
        "ts": 1234567890.0,
        "venue": "mexc",
        "symbol": "BTCUSDT",
        "last": 50000.0,
        "bid": 49999.0,
        "ask": 50001.0,
    }
    
    await set_last_tick("BTCUSDT", tick)
    
    # Verify it was stored
    from backend.src.infra.redis_stream import get_last_tick
    stored = await get_last_tick("BTCUSDT")
    
    assert stored is not None
    assert stored["symbol"] == "BTCUSDT"
    assert stored["last"] == 50000.0


@pytest.mark.asyncio
async def test_paper_engine_tick_update():
    """Test paper engine receives and processes ticks."""
    from backend.src.trading.paper_engine_rt import RealtimePaperEngine
    
    engine = RealtimePaperEngine(starting_balance=10000.0)
    
    # Send a tick
    tick = {
        "symbol": "BTCUSDT",
        "last": 50000.0,
    }
    
    await engine.on_tick(tick)
    
    # Verify tick was processed
    assert "BTCUSDT" in engine.last_tick_prices
    assert engine.last_tick_prices["BTCUSDT"] == 50000.0


@pytest.mark.asyncio
async def test_paper_engine_signal_execution():
    """Test paper engine executes signals correctly."""
    from backend.src.trading.paper_engine_rt import RealtimePaperEngine
    
    engine = RealtimePaperEngine(starting_balance=10000.0)
    
    # Setup: Send a tick first (so we have market data)
    await engine.on_tick({"symbol": "BTCUSDT", "last": 50000.0})
    
    # Execute buy signal
    signal = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "size": 0.1,  # 0.1 BTC
        "confidence": 0.8,
        "source": "test",
    }
    
    result = await engine.execute_signal(signal)
    
    assert result["ok"] is True
    assert result["symbol"] == "BTCUSDT"
    assert result["side"] == "buy"
    assert result["qty"] == 0.1
    
    # Verify position was opened
    stats = engine.get_portfolio_stats()
    assert stats["positions_count"] == 1
    assert len(stats["positions"]) == 1
    assert stats["positions"][0]["symbol"] == "BTCUSDT"


def test_symbol_normalization():
    """Test symbol normalization across exchanges."""
    from backend.src.market.normalize import denorm_symbol, norm_symbol
    
    # MEXC format
    assert norm_symbol("btcusdt", "mexc") == "BTCUSDT"
    assert norm_symbol("BTC_USDT", "mexc") == "BTCUSDT"
    
    # Reverse
    assert denorm_symbol("BTCUSDT", "mexc") == "btcusdt"


def test_slippage_calculation():
    """Test slippage and fee calculations."""
    from backend.src.trading.slippage import calculate_fee, slippage_price
    
    # Buy with slippage (should be higher)
    mark = 50000.0
    fill_buy = slippage_price(mark, "buy", qty=0.1)
    assert fill_buy > mark
    
    # Sell with slippage (should be lower)
    fill_sell = slippage_price(mark, "sell", qty=0.1)
    assert fill_sell < mark
    
    # Fee calculation
    notional = 5000.0
    fee = calculate_fee(notional, is_maker=False)
    assert fee > 0
    assert fee == notional * 0.0005  # 5 bps default


def test_risk_guard():
    """Test risk guard allows/blocks trades."""
    from backend.src.trading.risk_guard import RiskGuard
    
    guard = RiskGuard()
    
    # Should allow normal trade
    allowed, reason = guard.allow(1000.0)
    assert allowed is True
    
    # Should block oversized trade
    allowed, reason = guard.allow(5000.0)  # Exceeds MAX_POS_NOTIONAL=2000
    assert allowed is False
    assert "notional" in reason.lower()
    
    # Simulate daily loss
    guard.daily_realized = -250.0
    allowed, reason = guard.allow(100.0)  # Exceeds MAX_DAILY_LOSS=-200
    assert allowed is False
    assert "loss" in reason.lower()


@pytest.mark.asyncio
async def test_openai_signal_extraction():
    """Test OpenAI signal extraction (if API key available)."""
    import os

    from backend.src.ai.openai_client import extract_signal_from_text
    
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    text = "🚀 BTC LONG NOW! Entry: 50000, TP: 55000, SL: 48000. High confidence!"
    
    result = extract_signal_from_text(text)
    
    assert result["symbol"] in ["BTC", "BTCUSDT", "BTCUSD"]
    assert result["side"] in ["buy", "sell"]
    assert 0.0 <= result["confidence"] <= 1.0


def test_settings_loaded():
    """Test settings are properly loaded."""
    from backend.src.infra.settings import settings
    
    assert settings.PAPER is not None
    assert settings.EXCHANGE == "MEXC"
    assert settings.SLIPPAGE_BPS >= 0
    assert settings.FEE_TAKER_BPS >= 0
    assert settings.MAX_DAILY_LOSS < 0
    assert settings.MAX_POS_NOTIONAL > 0
    assert len(settings.SYMBOLS) > 0


if __name__ == "__main__":
    # Quick manual run
    pytest.main([__file__, "-v", "-s"])








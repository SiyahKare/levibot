"""
Integration Smoke Tests for Strategy Engines
"""
import time

import pytest


class TestLSESmoke:
    """LSE Engine smoke tests"""
    
    def test_lse_start_stop(self):
        """Test LSE engine can start and stop"""
        from backend.src.strategies.lse.engine import ENGINE
        
        # Start
        ENGINE.start(mode="paper")
        time.sleep(1)
        
        assert ENGINE.running() is True
        
        # Stop
        ENGINE.stop()
        assert ENGINE.running() is False
    
    def test_lse_features(self):
        """Test LSE features are calculated"""
        from backend.src.strategies.lse.engine import ENGINE
        
        ENGINE.start(mode="paper")
        time.sleep(3)  # Wait for features
        
        health = ENGINE.health()
        
        # Features should be calculated
        assert "features" in health
        assert health["features"]["atr"] is not None or health["features"]["zscore"] is not None
        
        ENGINE.stop()
    
    def test_lse_executor_integration(self):
        """Test LSE executor is integrated"""
        from backend.src.strategies.lse.engine import ENGINE
        
        assert ENGINE._executor is None  # Not initialized until start
        
        ENGINE.start(mode="paper")
        time.sleep(1)
        
        assert ENGINE._executor is not None
        assert ENGINE._executor.mode == "paper"
        
        ENGINE.stop()


class TestDayEngineSmoke:
    """Day Engine smoke tests"""
    
    def test_day_start_stop(self):
        """Test Day engine can start and stop"""
        from backend.src.strategies.day.engine import ENGINE
        
        ENGINE.start(mode="paper")
        time.sleep(1)
        assert ENGINE.running() is True
        
        ENGINE.stop()
        assert ENGINE.running() is False
    
    def test_day_features(self):
        """Test Day engine features"""
        from backend.src.strategies.day.engine import ENGINE
        
        ENGINE.start(mode="paper")
        time.sleep(8)  # Wait for features (slower update)
        
        health = ENGINE.health()
        
        # Features should exist
        assert "features" in health
        # EMA should be calculated
        assert health["features"]["ema_short"] is not None
        
        ENGINE.stop()


class TestSwingEngineSmoke:
    """Swing Engine smoke tests"""
    
    def test_swing_start_stop(self):
        """Test Swing engine can start and stop"""
        from backend.src.strategies.swing.engine import ENGINE
        
        ENGINE.start(mode="paper")
        time.sleep(1)
        assert ENGINE.running() is True
        
        ENGINE.stop()
        assert ENGINE.running() is False
    
    def test_swing_features(self):
        """Test Swing engine features"""
        from backend.src.strategies.swing.engine import ENGINE
        
        ENGINE.start(mode="paper")
        time.sleep(15)  # Wait for features (slower update)
        
        health = ENGINE.health()
        
        # Features should exist
        assert "features" in health
        assert health["features"]["ema_short"] is not None
        
        ENGINE.stop()


class TestMarketDataFeed:
    """Market data feed smoke tests"""
    
    @pytest.mark.asyncio
    async def test_websocket_feed(self):
        """Test WebSocket feed can start and emit ticks"""
        from backend.src.market_data import get_feed
        
        feed = get_feed("BTCUSDT")
        
        ticks = []
        
        def on_tick(tick):
            ticks.append(tick)
        
        feed.subscribe(on_tick)
        
        await feed.start()
        await asyncio.sleep(1.5)  # Wait for ~6 ticks (4 Hz)
        await feed.stop()
        
        assert len(ticks) >= 4, f"Expected at least 4 ticks, got {len(ticks)}"
        
        # Validate tick structure
        tick = ticks[0]
        assert "symbol" in tick
        assert "price" in tick
        assert "bid" in tick
        assert "ask" in tick
        assert tick["symbol"] == "BTCUSDT"


# Import asyncio for async test
import asyncio



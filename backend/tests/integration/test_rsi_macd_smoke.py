"""
RSI + MACD Strategy Smoke Tests
──────────────────────────────────────
Quick integration tests for RSI+MACD strategy.

Tests:
    1. Config loading (scalp/day/swing)
    2. Engine initialization
    3. Start/stop lifecycle
    4. Feature calculation
    5. Signal generation (mock data)
    6. API endpoints
"""

import time

import pytest
import yaml
from src.strategies.rsi_macd import RsiMacdConfig, RsiMacdEngine


def test_config_loading_scalp():
    """Test loading scalp config from YAML"""
    with open("configs/rsi_macd.scalp.yaml") as f:
        data = yaml.safe_load(f)
    
    config = RsiMacdConfig.from_dict(data)
    
    assert config.mode == "scalp"
    assert config.symbol == "BTCUSDT"
    assert config.tf == "1m"
    assert config.rsi.period == 14
    assert config.rsi.enter_above == 50
    assert config.macd.fast == 12
    assert config.macd.slow == 26
    assert config.macd.signal == 9
    assert config.risk.sl_atr_mult == 1.2
    assert config.risk.tp_atr_mult == 1.2
    assert config.sync_bars == 2
    assert config.cooldown_bars == 5


def test_config_loading_day():
    """Test loading day config from YAML"""
    with open("configs/rsi_macd.day.yaml") as f:
        data = yaml.safe_load(f)
    
    config = RsiMacdConfig.from_dict(data)
    
    assert config.mode == "day"
    assert config.tf == "15m"
    assert config.risk.sl_atr_mult == 1.5
    assert config.risk.tp_atr_mult == 2.0
    assert config.sync_bars == 3
    assert config.cooldown_bars == 8


def test_config_loading_swing():
    """Test loading swing config from YAML"""
    with open("configs/rsi_macd.swing.yaml") as f:
        data = yaml.safe_load(f)
    
    config = RsiMacdConfig.from_dict(data)
    
    assert config.mode == "swing"
    assert config.tf == "4h"
    assert config.risk.sl_atr_mult == 2.0
    assert config.risk.tp_atr_mult == 3.0
    assert config.filters.min_adx == 18
    assert config.sizing.r_per_trade == 0.5
    assert config.cooldown_bars == 0
    assert config.partial_take_profits == [1.0, 2.0]


def test_engine_initialization():
    """Test engine can be initialized"""
    config = RsiMacdConfig(mode="day", symbol="BTCUSDT", tf="15m")
    engine = RsiMacdEngine(config, mode="paper")
    
    assert engine is not None
    assert engine._cfg.mode == "day"
    assert engine._mode == "paper"
    assert engine._running is False


def test_engine_start_stop():
    """Test engine start/stop lifecycle"""
    config = RsiMacdConfig(mode="scalp", symbol="BTCUSDT", tf="1m")
    engine = RsiMacdEngine(config, mode="paper")
    
    # Start
    result = engine.start()
    assert result["status"] == "started"
    assert engine._running is True
    
    # Wait a bit for loop to run
    time.sleep(2.0)
    
    # Check health
    health = engine.health()
    assert health["running"] is True
    assert health["mode"] == "scalp"
    assert health["symbol"] == "BTCUSDT"
    assert "features" in health
    assert "rsi" in health["features"]
    assert "macd_hist" in health["features"]
    
    # Stop
    result = engine.stop()
    assert result["status"] == "stopped"
    assert engine._running is False


def test_feature_calculation():
    """Test RSI + MACD features are calculated"""
    config = RsiMacdConfig(mode="day", symbol="BTCUSDT", tf="15m")
    engine = RsiMacdEngine(config, mode="paper")
    
    # Start engine
    engine.start()
    time.sleep(3.0)  # Let it calculate features
    
    # Check features
    features = engine._features.get_latest()
    
    assert "rsi" in features
    assert "macd_line" in features
    assert "macd_signal" in features
    assert "macd_hist" in features
    assert "atr" in features
    assert "adx" in features
    
    # RSI should be between 0-100
    assert 0 <= features["rsi"] <= 100
    
    # ATR should be positive
    assert features["atr"] > 0
    
    # Stop engine
    engine.stop()


def test_params_get_set():
    """Test getting and setting parameters"""
    config = RsiMacdConfig(mode="day", symbol="BTCUSDT", tf="15m")
    engine = RsiMacdEngine(config, mode="paper")
    
    # Get params
    params = engine.get_params()
    assert params["mode"] == "day"
    assert params["symbol"] == "BTCUSDT"
    
    # Set params
    new_params = {"rsi.period": 21, "macd.fast": 10}
    result = engine.set_params(new_params)
    assert result["status"] == "updated"
    
    # Verify update
    updated_params = engine.get_params()
    assert updated_params["rsi"]["period"] == 21
    assert updated_params["macd"]["fast"] == 10


def test_pnl_tracking():
    """Test PnL tracking works"""
    config = RsiMacdConfig(mode="scalp", symbol="BTCUSDT", tf="1m")
    engine = RsiMacdEngine(config, mode="paper")
    
    # Start and run for a bit
    engine.start()
    time.sleep(5.0)
    
    # Check PnL
    pnl = engine.pnl()
    
    assert "total_pnl" in pnl
    assert "num_trades" in pnl
    assert "win_rate" in pnl
    assert "profit_factor" in pnl
    
    # PnL should be a number
    assert isinstance(pnl["total_pnl"], (int, float))
    assert isinstance(pnl["num_trades"], int)
    
    # Stop engine
    engine.stop()


@pytest.mark.asyncio
async def test_api_health_endpoint():
    """Test /strategy/rsi-macd/health endpoint"""
    from httpx import AsyncClient
    from src.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/strategy/rsi-macd/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "running" in data
        assert "mode" in data
        assert "symbol" in data


@pytest.mark.asyncio
async def test_api_params_endpoint():
    """Test /strategy/rsi-macd/params endpoint"""
    from httpx import AsyncClient
    from src.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/strategy/rsi-macd/params")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "mode" in data
        assert "rsi" in data
        assert "macd" in data
        assert "risk" in data


@pytest.mark.asyncio
async def test_api_load_preset():
    """Test /strategy/rsi-macd/load-preset endpoint"""
    from httpx import AsyncClient
    from src.app.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/strategy/rsi-macd/load-preset?mode=swing")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "loaded"
        assert data["mode"] == "swing"
        assert "config" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])



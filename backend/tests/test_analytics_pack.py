"""
Analytics Pack Tests
Tests for strategy PnL and trades endpoints
"""
import os

import requests

API = os.getenv("API_URL", "http://localhost:8000")


def test_pnl_by_strategy():
    """Test strategy PnL endpoint."""
    r = requests.get(f"{API}/analytics/pnl/by_strategy?window=24h")
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_pnl_by_strategy_7d():
    """Test strategy PnL endpoint with 7d window."""
    r = requests.get(f"{API}/analytics/pnl/by_strategy?window=7d")
    assert r.status_code == 200
    data = r.json()
    assert data.get("window") == "7d"


def test_trades_recent():
    """Test recent trades endpoint."""
    r = requests.get(f"{API}/analytics/trades/recent?limit=10")
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_trades_recent_limit():
    """Test recent trades endpoint with custom limit."""
    r = requests.get(f"{API}/analytics/trades/recent?limit=50")
    assert r.status_code == 200
    data = r.json()
    assert len(data["items"]) <= 50


if __name__ == "__main__":
    print("Testing Analytics Pack endpoints...")
    
    try:
        test_pnl_by_strategy()
        print("✅ test_pnl_by_strategy passed")
    except Exception as e:
        print(f"❌ test_pnl_by_strategy failed: {e}")
    
    try:
        test_pnl_by_strategy_7d()
        print("✅ test_pnl_by_strategy_7d passed")
    except Exception as e:
        print(f"❌ test_pnl_by_strategy_7d failed: {e}")
    
    try:
        test_trades_recent()
        print("✅ test_trades_recent passed")
    except Exception as e:
        print(f"❌ test_trades_recent failed: {e}")
    
    try:
        test_trades_recent_limit()
        print("✅ test_trades_recent_limit passed")
    except Exception as e:
        print(f"❌ test_trades_recent_limit failed: {e}")
    
    print("\n✅ Analytics Pack tests completed!")


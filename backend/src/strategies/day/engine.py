"""
Daytrade Engine v1.0
Intraday momentum strategy with EMA, RSI, ADX
"""
import threading
import time

import numpy as np

from ..base import Mode, StrategyEngine
from .config import StrategyConfig
from .features import (
    DayFeatureCache,
)


class DayEngine(StrategyEngine):
    """Daytrade engine - intraday momentum (5m-15m)"""

    name = "day"

    def __init__(self):
        self._cfg = StrategyConfig()
        self._running = False
        self._mode: Mode = "paper"
        self._thread: threading.Thread | None = None
        self._last_loop_ms = None
        
        # Features cache
        self._features = DayFeatureCache()
        
        # Mock market data (will be replaced with real feed)
        # Start with 100 data points for immediate feature calculation
        base_price = 50000.0
        self._mock_prices = base_price + np.random.randn(100) * 200
        self._mock_highs = self._mock_prices + np.abs(np.random.randn(100) * 30)
        self._mock_lows = self._mock_prices - np.abs(np.random.randn(100) * 30)
        
        # Trade log
        self._trades = []
        self._pnl = 0.0

    def start(self, mode: Mode | None = None, overrides: dict | None = None) -> None:
        if self._running:
            return
        if mode:
            self._mode = mode
        if overrides:
            self.update_params(overrides)
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def running(self) -> bool:
        return self._running

    def params(self) -> dict:
        return self._cfg.__dict__

    def update_params(self, p: dict) -> dict:
        for k, v in p.items():
            if hasattr(self._cfg, k):
                setattr(self._cfg, k, v)
        return self.params()

    def _run_loop(self):
        """Main engine loop with feature calculation"""
        while self._running:
            t0 = time.perf_counter()
            
            # Slower loop for day trading (5 sec updates)
            time.sleep(5.0)
            
            # 1. Update mock market data
            self._update_mock_data()
            
            # 2. Calculate features
            current_ts = time.time()
            if self._features.is_stale(current_ts, ttl_sec=60.0):  # 1 min TTL
                self._calculate_features(current_ts)
            
            self._last_loop_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    def _update_mock_data(self):
        """Update mock market data"""
        change = np.random.randn() * 50 + 2  # Slight upward bias
        new_price = self._mock_prices[-1] + change
        
        self._mock_prices = np.append(self._mock_prices[-200:], new_price)
        self._mock_highs = np.append(self._mock_highs[-200:], new_price + abs(np.random.randn() * 30))
        self._mock_lows = np.append(self._mock_lows[-200:], new_price - abs(np.random.randn() * 30))
    
    def _calculate_features(self, ts: float):
        """Calculate day trading features (EMA, RSI, Donchian, ADX)"""
        from .features import (
            calculate_adx,
            calculate_donchian_channels,
            calculate_ema,
            calculate_rsi,
        )
        
        if len(self._mock_prices) < 50:
            return
        
        # EMA crossover (20/50)
        ema_short = calculate_ema(self._mock_prices, getattr(self._cfg, "ema_fast", 20))
        ema_long = calculate_ema(self._mock_prices, getattr(self._cfg, "ema_slow", 50))
        
        # RSI
        rsi = calculate_rsi(self._mock_prices, getattr(self._cfg, "rsi_period", 14))
        
        # Donchian Channels
        donchian = calculate_donchian_channels(self._mock_highs, self._mock_lows, period=20)
        
        # ADX (trend strength)
        adx = calculate_adx(self._mock_highs, self._mock_lows, self._mock_prices, period=14)
        
        self._features.update(
            ts=ts,
            ema_short=ema_short,
            ema_long=ema_long,
            rsi=rsi,
            donchian=donchian,
            adx=adx
        )

    def health(self) -> dict:
        """Get health status with features"""
        return {
            "running": self._running,
            "mode": self._mode,
            "symbol": self._cfg.symbol,
            "base_tf": self._cfg.base_tf,
            "latency_ms": self._last_loop_ms,
            "features": {
                "ema_short": self._features.ema_short,
                "ema_long": self._features.ema_long,
                "rsi": self._features.rsi,
                "donchian": self._features.donchian,
                "adx": self._features.adx,
                "last_update": self._features.last_update
            },
            "guards": {
                "vol_ok": True,
                "spread_ok": True,
                "latency_ok": True,
                "risk_ok": True,
            },
        }

    # API helpers
    def pnl(self) -> dict:
        return {"realized_pnl": self._pnl, "trades": len(self._trades)}

    def trades_recent(self, limit: int = 100) -> list:
        return list(reversed(self._trades))[:limit]


# Singleton instance
ENGINE = DayEngine()


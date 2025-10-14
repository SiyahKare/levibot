"""
Top Volume Tracker & Dynamic Universe Rotation
Tracks real-time volume metrics and ranks symbols
"""
import time
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class VolumeMetrics:
    """Volume metrics for a symbol"""
    symbol: str
    vol_usdt_15m: float = 0.0
    vol_usdt_1h: float = 0.0
    trades_15m: int = 0
    trades_1h: int = 0
    realized_vol_15m: float = 0.0  # Std dev of returns
    score: float = 0.0
    last_update: float = field(default_factory=time.time)


class TopVolTracker:
    """Track and rank symbols by volume metrics"""
    
    def __init__(
        self,
        w_15m: float = 0.6,
        w_1h: float = 0.3,
        w_rvol: float = 0.1
    ):
        """
        Initialize tracker with scoring weights
        
        Args:
            w_15m: Weight for 15m volume
            w_1h: Weight for 1h volume
            w_rvol: Weight for realized volatility
        """
        self.w_15m = w_15m
        self.w_1h = w_1h
        self.w_rvol = w_rvol
        self._metrics: dict[str, VolumeMetrics] = {}
    
    def update_metrics(
        self,
        symbol: str,
        vol_usdt_15m: float = 0.0,
        vol_usdt_1h: float = 0.0,
        trades_15m: int = 0,
        trades_1h: int = 0,
        realized_vol_15m: float = 0.0
    ):
        """Update metrics for a symbol"""
        # Calculate score
        score = (
            self.w_15m * vol_usdt_15m +
            self.w_1h * vol_usdt_1h +
            self.w_rvol * realized_vol_15m * 1000  # Scale rvol
        )
        
        self._metrics[symbol] = VolumeMetrics(
            symbol=symbol,
            vol_usdt_15m=vol_usdt_15m,
            vol_usdt_1h=vol_usdt_1h,
            trades_15m=trades_15m,
            trades_1h=trades_1h,
            realized_vol_15m=realized_vol_15m,
            score=score,
            last_update=time.time()
        )
    
    def get_top_n(self, n: int = 12) -> list[VolumeMetrics]:
        """Get top N symbols by score"""
        sorted_metrics = sorted(
            self._metrics.values(),
            key=lambda m: m.score,
            reverse=True
        )
        return sorted_metrics[:n]
    
    def get_metrics(self, symbol: str) -> VolumeMetrics | None:
        """Get metrics for a specific symbol"""
        return self._metrics.get(symbol)
    
    def get_all_metrics(self) -> dict[str, VolumeMetrics]:
        """Get all metrics"""
        return self._metrics.copy()


# Global tracker instance
_tracker: TopVolTracker | None = None


def get_topvol_tracker() -> TopVolTracker:
    """Get or create global top vol tracker"""
    global _tracker
    if _tracker is None:
        _tracker = TopVolTracker()
    return _tracker


async def compute_volume_metrics_from_db(
    symbols: list[str],
    window: Literal["15m", "1h"] = "15m"
) -> dict[str, VolumeMetrics]:
    """
    Compute volume metrics from TimescaleDB
    
    This is a placeholder - integrate with your actual DB
    """
    # TODO: Query TimescaleDB market_ticks
    # For now, return mock data
    
    metrics = {}
    for symbol in symbols:
        # Mock data - replace with actual DB query
        vol_15m = 1000000.0 + hash(symbol) % 5000000
        vol_1h = vol_15m * 3.5
        trades_15m = 500 + hash(symbol) % 2000
        
        metrics[symbol] = VolumeMetrics(
            symbol=symbol,
            vol_usdt_15m=vol_15m,
            vol_usdt_1h=vol_1h,
            trades_15m=trades_15m,
            trades_1h=trades_15m * 4,
            realized_vol_15m=0.015 + (hash(symbol) % 100) / 10000,
            score=0.0  # Will be calculated by tracker
        )
    
    return metrics


async def update_topvol_tracker(symbols: list[str]):
    """Update tracker with latest metrics from DB"""
    tracker = get_topvol_tracker()
    metrics = await compute_volume_metrics_from_db(symbols)
    
    for symbol, metric in metrics.items():
        tracker.update_metrics(
            symbol=symbol,
            vol_usdt_15m=metric.vol_usdt_15m,
            vol_usdt_1h=metric.vol_usdt_1h,
            trades_15m=metric.trades_15m,
            trades_1h=metric.trades_1h,
            realized_vol_15m=metric.realized_vol_15m
        )


"""
LSE Features Module
Fast feature calculation for scalp/volatility trading
"""

import numpy as np


def calculate_atr(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14
) -> float:
    """
    Calculate Average True Range

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period (default 14)

    Returns:
        Current ATR value
    """
    if len(high) < period + 1:
        return 0.0

    # True Range components
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))

    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr = tr[1:]  # Remove first element (rolled)

    # Simple moving average of TR
    atr = np.mean(tr[-period:])
    return float(atr)


def calculate_zscore(prices: np.ndarray, lookback: int = 120) -> float:
    """
    Calculate Z-score for mean reversion signal

    Args:
        prices: Price array
        lookback: Lookback period

    Returns:
        Current Z-score
    """
    if len(prices) < lookback:
        return 0.0

    window = prices[-lookback:]
    mean = np.mean(window)
    std = np.std(window)

    if std == 0:
        return 0.0

    current = prices[-1]
    zscore = (current - mean) / std
    return float(zscore)


def calculate_realized_vol(returns: np.ndarray, window: int = 60) -> float:
    """
    Calculate realized volatility from returns

    Args:
        returns: Return array
        window: Window size (in ticks/bars)

    Returns:
        Realized volatility (annualized if needed)
    """
    if len(returns) < window:
        return 0.0

    window_returns = returns[-window:]
    vol = np.std(window_returns) * np.sqrt(window)  # Scaled volatility
    return float(vol)


def calculate_spread_bps(bid: float, ask: float) -> float:
    """
    Calculate bid-ask spread in basis points

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Spread in bps
    """
    if bid <= 0 or ask <= 0:
        return 999.0  # Invalid

    mid = (bid + ask) / 2
    spread = (ask - bid) / mid * 10000  # bps
    return spread


class FeatureCache:
    """Cache for computed features (reduces redundant calculations)"""

    def __init__(self):
        self.atr: float | None = None
        self.zscore: float | None = None
        self.vol: float | None = None
        self.spread_bps: float | None = None
        self.last_update_ts: float | None = None

    def is_stale(self, current_ts: float, ttl_sec: float = 1.0) -> bool:
        """Check if cache is stale"""
        if self.last_update_ts is None:
            return True
        return (current_ts - self.last_update_ts) > ttl_sec

    def update(
        self,
        ts: float,
        atr: float | None = None,
        zscore: float | None = None,
        vol: float | None = None,
        spread_bps: float | None = None,
    ):
        """Update cached features"""
        self.last_update_ts = ts
        if atr is not None:
            self.atr = atr
        if zscore is not None:
            self.zscore = zscore
        if vol is not None:
            self.vol = vol
        if spread_bps is not None:
            self.spread_bps = spread_bps

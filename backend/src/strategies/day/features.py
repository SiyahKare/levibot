"""
Day Trading Features - Technical Indicators
EMA, RSI, Donchian Channels, ADX
"""

import numpy as np


def calculate_ema(prices: np.ndarray, period: int) -> float:
    """
    Calculate Exponential Moving Average.

    Args:
        prices: Array of prices
        period: EMA period

    Returns:
        Current EMA value
    """
    if len(prices) < period:
        return np.mean(prices) if len(prices) > 0 else 0.0

    # Calculate EMA using pandas-style algorithm
    multiplier = 2.0 / (period + 1)
    ema = prices[0]

    for price in prices[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))

    return float(ema)


def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
    """
    Calculate Relative Strength Index.

    Args:
        prices: Array of prices
        period: RSI period (default: 14)

    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral

    # Calculate price changes
    deltas = np.diff(prices)

    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    # Calculate average gains and losses
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return float(rsi)


def calculate_donchian_channels(
    highs: np.ndarray, lows: np.ndarray, period: int = 20
) -> dict:
    """
    Calculate Donchian Channels.

    Args:
        highs: Array of high prices
        lows: Array of low prices
        period: Channel period (default: 20)

    Returns:
        Dict with upper, lower, and middle channel values
    """
    if len(highs) < period or len(lows) < period:
        # Return current price as all bands
        current_high = highs[-1] if len(highs) > 0 else 0.0
        current_low = lows[-1] if len(lows) > 0 else 0.0
        middle = (current_high + current_low) / 2

        return {
            "upper": float(current_high),
            "lower": float(current_low),
            "middle": float(middle),
        }

    upper = float(np.max(highs[-period:]))
    lower = float(np.min(lows[-period:]))
    middle = (upper + lower) / 2

    return {"upper": upper, "lower": lower, "middle": middle}


def calculate_adx(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
) -> float:
    """
    Calculate Average Directional Index (ADX).

    Args:
        highs: Array of high prices
        lows: Array of low prices
        closes: Array of close prices
        period: ADX period (default: 14)

    Returns:
        ADX value (0-100)
    """
    if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
        return 0.0

    # Calculate True Range
    tr1 = highs[1:] - lows[1:]
    tr2 = np.abs(highs[1:] - closes[:-1])
    tr3 = np.abs(lows[1:] - closes[:-1])
    tr = np.maximum(tr1, np.maximum(tr2, tr3))

    # Calculate Directional Movement
    up_move = highs[1:] - highs[:-1]
    down_move = lows[:-1] - lows[1:]

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)

    # Smooth the values
    if len(tr) < period:
        return 0.0

    atr = np.mean(tr[-period:])
    plus_di = 100 * np.mean(plus_dm[-period:]) / atr if atr > 0 else 0
    minus_di = 100 * np.mean(minus_dm[-period:]) / atr if atr > 0 else 0

    # Calculate DX and ADX
    dx = (
        100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        if (plus_di + minus_di) > 0
        else 0
    )

    # Simple average for ADX (should be EMA in production)
    adx = float(dx)

    return adx


class DayFeatureCache:
    """
    Cache for day trading features.
    Similar to LSE FeatureCache but for day trading indicators.
    """

    def __init__(self):
        self.ema_short: float | None = None
        self.ema_long: float | None = None
        self.rsi: float | None = None
        self.donchian: dict | None = None
        self.adx: float | None = None
        self.last_update: float | None = None

    def update(
        self,
        ts: float,
        ema_short: float | None = None,
        ema_long: float | None = None,
        rsi: float | None = None,
        donchian: dict | None = None,
        adx: float | None = None,
    ):
        """Update cached features."""
        if ema_short is not None:
            self.ema_short = ema_short
        if ema_long is not None:
            self.ema_long = ema_long
        if rsi is not None:
            self.rsi = rsi
        if donchian is not None:
            self.donchian = donchian
        if adx is not None:
            self.adx = adx

        self.last_update = ts

    def is_stale(self, current_ts: float, ttl_sec: float = 60.0) -> bool:
        """Check if features are stale."""
        if self.last_update is None:
            return True
        return (current_ts - self.last_update) > ttl_sec

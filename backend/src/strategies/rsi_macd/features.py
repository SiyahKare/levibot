"""
RSI + MACD Feature Calculations
"""

from collections import deque

import numpy as np


def calculate_rsi(prices: np.ndarray, period: int = 14) -> float:
    """
    Calculate RSI (Relative Strength Index).

    Args:
        prices: Array of close prices (most recent last)
        period: RSI period (default 14)

    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral default

    deltas = np.diff(prices[-period - 1 :])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


def calculate_macd(
    prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9
) -> dict:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: Array of close prices
        fast: Fast EMA period
        slow: Slow EMA period
        signal: Signal line EMA period

    Returns:
        dict with keys: macd_line, signal_line, histogram
    """
    if len(prices) < slow + signal:
        return {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}

    # Calculate EMAs
    ema_fast = _ema(prices, fast)
    ema_slow = _ema(prices, slow)

    # MACD line = fast EMA - slow EMA
    macd_line = ema_fast - ema_slow

    # Calculate signal line (EMA of MACD line)
    # For simplicity, use last N MACD values
    macd_history = []
    for i in range(max(slow, signal), len(prices)):
        f = _ema(prices[: i + 1], fast)
        s = _ema(prices[: i + 1], slow)
        macd_history.append(f - s)

    if len(macd_history) < signal:
        signal_line = macd_line
    else:
        signal_line = _ema(np.array(macd_history), signal)

    histogram = macd_line - signal_line

    return {
        "macd_line": float(macd_line),
        "signal_line": float(signal_line),
        "histogram": float(histogram),
    }


def calculate_atr(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
) -> float:
    """
    Calculate ATR (Average True Range).

    Args:
        highs: Array of high prices
        lows: Array of low prices
        closes: Array of close prices
        period: ATR period

    Returns:
        ATR value
    """
    if len(closes) < period + 1:
        return (highs[-1] - lows[-1]) if len(highs) > 0 else 0.0

    # True Range = max(high - low, |high - prev_close|, |low - prev_close|)
    tr = []
    for i in range(1, len(closes)):
        h = highs[i]
        l = lows[i]
        pc = closes[i - 1]
        tr.append(max(h - l, abs(h - pc), abs(l - pc)))

    atr = np.mean(tr[-period:])
    return float(atr)


def calculate_adx(
    highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14
) -> float:
    """
    Calculate ADX (Average Directional Index) - simplified version.

    Returns:
        ADX value (0-100), measures trend strength
    """
    if len(closes) < period + 1:
        return 0.0

    # Simplified: use volatility as proxy for trend strength
    returns = np.diff(closes[-period:]) / closes[-period - 1 : -1]
    volatility = np.std(returns) * np.sqrt(252)  # Annualized

    # Map volatility to 0-100 scale (higher vol = higher ADX)
    adx = min(100.0, volatility * 100)
    return float(adx)


def _ema(data: np.ndarray, period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(data) < period:
        return float(np.mean(data)) if len(data) > 0 else 0.0

    alpha = 2.0 / (period + 1)
    ema = data[0]
    for price in data[1:]:
        ema = alpha * price + (1 - alpha) * ema
    return float(ema)


class RsiMacdFeatureCache:
    """
    Cache for RSI + MACD features with rolling window.
    """

    def __init__(self, max_history: int = 200):
        self.max_history = max_history
        self.prices = deque(maxlen=max_history)
        self.highs = deque(maxlen=max_history)
        self.lows = deque(maxlen=max_history)

        self.last_rsi = 50.0
        self.last_macd = {"macd_line": 0.0, "signal_line": 0.0, "histogram": 0.0}
        self.last_atr = 0.0
        self.last_adx = 0.0

        # For sync detection
        self.last_macd_cross_bar = -999
        self.last_rsi_cross_bar = -999
        self.current_bar = 0

    def update(
        self,
        price: float,
        high: float,
        low: float,
        rsi_period: int = 14,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        atr_period: int = 14,
    ) -> dict:
        """
        Update all features with new bar data.

        Returns:
            dict with all calculated features
        """
        self.prices.append(price)
        self.highs.append(high)
        self.lows.append(low)
        self.current_bar += 1

        prices_arr = np.array(self.prices)
        highs_arr = np.array(self.highs)
        lows_arr = np.array(self.lows)

        # Calculate features
        prev_rsi = self.last_rsi
        prev_macd_hist = self.last_macd["histogram"]

        self.last_rsi = calculate_rsi(prices_arr, rsi_period)
        self.last_macd = calculate_macd(prices_arr, macd_fast, macd_slow, macd_signal)
        self.last_atr = calculate_atr(highs_arr, lows_arr, prices_arr, atr_period)
        self.last_adx = calculate_adx(highs_arr, lows_arr, prices_arr, 14)

        # Detect crosses
        rsi_crossed_up = prev_rsi <= 50.0 and self.last_rsi > 50.0
        rsi_crossed_down = prev_rsi >= 50.0 and self.last_rsi < 50.0

        macd_hist_crossed_up = (
            prev_macd_hist <= 0.0 and self.last_macd["histogram"] > 0.0
        )
        macd_hist_crossed_down = (
            prev_macd_hist >= 0.0 and self.last_macd["histogram"] < 0.0
        )

        if rsi_crossed_up or rsi_crossed_down:
            self.last_rsi_cross_bar = self.current_bar

        if macd_hist_crossed_up or macd_hist_crossed_down:
            self.last_macd_cross_bar = self.current_bar

        return {
            "rsi": self.last_rsi,
            "rsi_prev": prev_rsi,
            "macd_line": self.last_macd["macd_line"],
            "macd_signal": self.last_macd["signal_line"],
            "macd_hist": self.last_macd["histogram"],
            "macd_hist_prev": prev_macd_hist,
            "atr": self.last_atr,
            "adx": self.last_adx,
            "rsi_crossed_up": rsi_crossed_up,
            "rsi_crossed_down": rsi_crossed_down,
            "macd_crossed_up": macd_hist_crossed_up,
            "macd_crossed_down": macd_hist_crossed_down,
            "sync_bars_since_rsi": self.current_bar - self.last_rsi_cross_bar,
            "sync_bars_since_macd": self.current_bar - self.last_macd_cross_bar,
        }

    def get_latest(self) -> dict:
        """Get latest cached features"""
        return {
            "rsi": self.last_rsi,
            "macd_line": self.last_macd["macd_line"],
            "macd_signal": self.last_macd["signal_line"],
            "macd_hist": self.last_macd["histogram"],
            "atr": self.last_atr,
            "adx": self.last_adx,
        }

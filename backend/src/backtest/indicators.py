"""Technical indicators for backtesting strategies."""

from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        close: Close price series
        period: RSI period (default: 14)
        
    Returns:
        RSI series (0-100 range)
    """
    delta = close.diff()
    up = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = up / (down.replace(0, 1e-9))
    return (100 - (100 / (1 + rs))).fillna(50)


def sma(close: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average.
    
    Args:
        close: Close price series
        period: SMA period
        
    Returns:
        SMA series
    """
    return close.rolling(period).mean()


def ema(close: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average.
    
    Args:
        close: Close price series
        period: EMA period
        
    Returns:
        EMA series
    """
    return close.ewm(span=period, adjust=False).mean()


def macd(
    close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    MACD (Moving Average Convergence Divergence).
    
    Args:
        close: Close price series
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line period (default: 9)
        
    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    ema_fast = ema(close, fast)
    ema_slow = ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(
    close: pd.Series, period: int = 20, std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.
    
    Args:
        close: Close price series
        period: SMA period (default: 20)
        std: Standard deviation multiplier (default: 2.0)
        
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle = sma(close, period)
    std_dev = close.rolling(period).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    return upper, middle, lower


import numpy as np
import pandas as pd

from .ta import ema, rsi, sma


def sma_strategy(df: pd.DataFrame, fast: int = 10, slow: int = 50):
    """SMA crossover strategy"""
    close = df["close"]
    fast_sma = sma(close, fast)
    slow_sma = sma(close, slow)

    # Generate signals
    signals = []
    orders = []

    for i in range(len(df)):
        if i < slow:  # Not enough data
            signals.append(0)
            continue

        if (
            fast_sma.iloc[i] > slow_sma.iloc[i]
            and fast_sma.iloc[i - 1] <= slow_sma.iloc[i - 1]
        ):
            signals.append(1)  # Buy signal
            orders.append(
                {
                    "pair": "BTCUSDT",
                    "side": "BUY",
                    "qty": 0.1,
                    "kind": "MARKET",
                    "reason": f"sma_cross_fast{fast}_slow{slow}",
                }
            )
        elif (
            fast_sma.iloc[i] < slow_sma.iloc[i]
            and fast_sma.iloc[i - 1] >= slow_sma.iloc[i - 1]
        ):
            signals.append(-1)  # Sell signal
            orders.append(
                {
                    "pair": "BTCUSDT",
                    "side": "SELL",
                    "qty": 0.1,
                    "kind": "MARKET",
                    "reason": f"sma_cross_fast{fast}_slow{slow}",
                }
            )
        else:
            signals.append(0)

    # Simple equity curve (cumulative returns)
    equity = np.cumsum(signals) * 0.01  # 1% per signal

    return equity.tolist(), orders


def ema_strategy(df: pd.DataFrame, fast: int = 12, slow: int = 26):
    """EMA crossover strategy"""
    close = df["close"]
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)

    signals = []
    orders = []

    for i in range(len(df)):
        if i < slow:
            signals.append(0)
            continue

        if (
            fast_ema.iloc[i] > slow_ema.iloc[i]
            and fast_ema.iloc[i - 1] <= slow_ema.iloc[i - 1]
        ):
            signals.append(1)
            orders.append(
                {
                    "pair": "ETHUSDT",
                    "side": "BUY",
                    "qty": 0.1,
                    "kind": "MARKET",
                    "reason": f"ema_cross_fast{fast}_slow{slow}",
                }
            )
        elif (
            fast_ema.iloc[i] < slow_ema.iloc[i]
            and fast_ema.iloc[i - 1] >= slow_ema.iloc[i - 1]
        ):
            signals.append(-1)
            orders.append(
                {
                    "pair": "ETHUSDT",
                    "side": "SELL",
                    "qty": 0.1,
                    "kind": "MARKET",
                    "reason": f"ema_cross_fast{fast}_slow{slow}",
                }
            )
        else:
            signals.append(0)

    equity = np.cumsum(signals) * 0.01
    return equity.tolist(), orders


def rsi_strategy(
    df: pd.DataFrame, period: int = 14, oversold: int = 30, overbought: int = 70
):
    """RSI strategy"""
    close = df["close"]
    rsi_values = rsi(close, period)

    signals = []
    orders = []

    for i in range(len(df)):
        if i < period:
            signals.append(0)
            continue

        if rsi_values.iloc[i] < oversold and rsi_values.iloc[i - 1] >= oversold:
            signals.append(1)  # Buy
            orders.append(
                {
                    "pair": "BTCUSDT",
                    "side": "BUY",
                    "qty": 0.1,
                    "kind": "MARKET",
                    "reason": f"rsi_oversold_{oversold}",
                }
            )
        elif rsi_values.iloc[i] > overbought and rsi_values.iloc[i - 1] <= overbought:
            signals.append(-1)  # Sell
            orders.append(
                {
                    "pair": "BTCUSDT",
                    "side": "SELL",
                    "qty": 0.1,
                    "kind": "MARKET",
                    "reason": f"rsi_overbought_{overbought}",
                }
            )
        else:
            signals.append(0)

    equity = np.cumsum(signals) * 0.01
    return equity.tolist(), orders


STRATEGIES = {
    "sma": sma_strategy,
    "ema": ema_strategy,
    "rsi": rsi_strategy,
}

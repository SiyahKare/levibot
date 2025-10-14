"""Vectorized backtest runner with realistic fills and costs."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd

from .metrics import hitrate, max_drawdown, sharpe, sortino, turnover


def _mid(
    o: np.ndarray, h: np.ndarray, l: np.ndarray, c: np.ndarray
) -> np.ndarray:
    """Calculate mid-price from OHLC."""
    return (o + h + l + c) / 4.0


def run_backtest(
    bars: pd.DataFrame,
    signal_fn: Callable[[pd.DataFrame], pd.Series],
    fee_bps: float = 5.0,
    slippage_bps: float = 5.0,
    max_pos: int = 1,
) -> dict[str, Any]:
    """
    Run vectorized backtest with realistic fills and transaction costs.

    Strategy Logic:
        - prob_up >= 0.5 → long (position=1)
        - prob_up < 0.5 → flat (position=0)

    Fill Logic:
        - Entry/exit at t+1 mid-price
        - Costs: fee + slippage (basis points)

    Args:
        bars: DataFrame with columns [ts, open, high, low, close, volume]
        signal_fn: Function that takes bars and returns prob_up (0..1)
        fee_bps: Trading fee in basis points (e.g., 5 = 0.05%)
        slippage_bps: Slippage cost in basis points
        max_pos: Maximum position size (default: 1)

    Returns:
        Dictionary containing:
            - equity: Cumulative equity curve
            - pnl: Per-period P&L series
            - side: Position array (0=flat, 1=long)
            - prob: Signal probabilities
            - metrics: Dict with sharpe, sortino, mdd, hitrate, etc.
    """
    df = bars.copy().reset_index(drop=True)
    df = df[["ts", "open", "high", "low", "close", "volume"]].astype(float)

    mid = _mid(
        df["open"].values,
        df["high"].values,
        df["low"].values,
        df["close"].values,
    )

    # Generate signals
    prob = signal_fn(df).values.astype(float)
    prob = np.nan_to_num(prob, nan=0.5)

    # Position: long if prob >= 0.5, else flat
    side = (prob >= 0.5).astype(int)  # 1=long, 0=flat
    side = np.clip(side, 0, max_pos)

    # Fill at t+1 mid-price
    entry_price = np.roll(mid, -1)
    exit_price = np.roll(mid, -1)

    # Per-minute return (if holding long)
    ret = np.zeros_like(mid)
    ret[:-1] = (exit_price[:-1] - mid[:-1]) / (mid[:-1] + 1e-12)

    # Gross P&L (long only, flat = 0)
    gross = ret * side

    # Transaction costs (applied on position changes)
    cost = (fee_bps + slippage_bps) * 1e-4 * np.abs(np.diff(side, prepend=0))

    # Net P&L
    pnl = gross - cost

    # Equity curve
    equity = (1.0 + pnl).cumprod()

    # Trade-level P&L (approximation: sum pnl during position changes)
    trades_pnl = pnl[np.diff(side, prepend=0) != 0]

    # Metrics
    metrics = {
        "sharpe": sharpe(pnl),
        "sortino": sortino(pnl),
        "max_drawdown": max_drawdown(equity),
        "hitrate": hitrate(trades_pnl),
        "turnover": turnover(side),
        "cum_return_pct": float(equity[-1] - 1.0) * 100.0,
        "n_minutes": int(len(df)),
        "n_trades": int(np.abs(np.diff(side, prepend=0)).sum()),
    }

    return {
        "equity": equity,
        "pnl": pnl,
        "side": side,
        "prob": prob,
        "metrics": metrics,
    }


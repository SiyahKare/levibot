"""Backtest performance metrics calculation."""

from __future__ import annotations

import numpy as np


def _dd_curve(equity: np.ndarray) -> np.ndarray:
    """Calculate drawdown curve from equity series."""
    peak = np.maximum.accumulate(equity)
    return (equity - peak) / (peak + 1e-12)


def max_drawdown(equity: np.ndarray) -> float:
    """
    Calculate maximum drawdown from equity curve.

    Returns:
        Negative float representing max drawdown (e.g., -0.15 = -15%)
    """
    return float(_dd_curve(equity).min())


def sharpe(returns: np.ndarray, eps: float = 1e-12) -> float:
    """
    Calculate annualized Sharpe ratio.

    Assumes returns are per-minute, annualizes to 525,600 minutes/year.

    Args:
        returns: Array of per-period returns
        eps: Small value to avoid division by zero

    Returns:
        Annualized Sharpe ratio
    """
    mu = returns.mean()
    sd = returns.std() + eps
    # minute → year scale (~365*24*60 ≈ 525600)
    ann_return = mu * 525600
    ann_sd = sd * (525600**0.5)
    return float(ann_return / (ann_sd + eps))


def sortino(returns: np.ndarray, eps: float = 1e-12) -> float:
    """
    Calculate annualized Sortino ratio (downside deviation only).

    Args:
        returns: Array of per-period returns
        eps: Small value to avoid division by zero

    Returns:
        Annualized Sortino ratio
    """
    neg = returns[returns < 0]
    if neg.size == 0:
        return float("inf")
    dn = neg.std() + eps
    mu = returns.mean()
    ann_return = mu * 525600
    ann_dn = dn * (525600**0.5)
    return float(ann_return / (ann_dn + eps))


def hitrate(trades_pnl: np.ndarray) -> float:
    """
    Calculate win rate from trade P&L array.

    Args:
        trades_pnl: Array of trade-level P&L values

    Returns:
        Win rate as fraction (0.0 to 1.0)
    """
    if trades_pnl.size == 0:
        return 0.0
    return float((trades_pnl > 0).mean())


def turnover(positions: np.ndarray) -> float:
    """
    Calculate total position turnover.

    Args:
        positions: Array of position sizes over time

    Returns:
        Sum of absolute position changes
    """
    chg = np.abs(np.diff(positions, prepend=0))
    return float(chg.sum())


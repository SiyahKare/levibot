"""
Backtest performance metrics.

Metrics:
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown (MDD)
- CAGR (Compound Annual Growth Rate)
- Hit Rate
- Turnover
- Cumulative Return
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_returns(equity_curve: np.ndarray) -> np.ndarray:
    """Calculate returns from equity curve."""
    returns = np.diff(equity_curve) / equity_curve[:-1]
    return returns


def sharpe_ratio(returns: np.ndarray, periods_per_year: int = 525600) -> float:
    """
    Calculate Sharpe Ratio.

    Args:
        returns: Array of returns
        periods_per_year: For 1m bars: 525600 (365.25 * 24 * 60)

    Returns:
        Sharpe ratio (annualized)
    """
    if len(returns) == 0:
        return 0.0

    mean_return = np.mean(returns)
    std_return = np.std(returns)

    if std_return == 0:
        return 0.0

    sharpe = mean_return / std_return * np.sqrt(periods_per_year)
    return float(sharpe)


def sortino_ratio(returns: np.ndarray, periods_per_year: int = 525600) -> float:
    """
    Calculate Sortino Ratio (downside deviation only).

    Args:
        returns: Array of returns
        periods_per_year: For 1m bars: 525600

    Returns:
        Sortino ratio (annualized)
    """
    if len(returns) == 0:
        return 0.0

    mean_return = np.mean(returns)
    downside_returns = returns[returns < 0]

    if len(downside_returns) == 0:
        return 0.0

    downside_std = np.std(downside_returns)

    if downside_std == 0:
        return 0.0

    sortino = mean_return / downside_std * np.sqrt(periods_per_year)
    return float(sortino)


def maximum_drawdown(equity_curve: np.ndarray) -> float:
    """
    Calculate Maximum Drawdown.

    Args:
        equity_curve: Array of equity values

    Returns:
        Maximum drawdown (0.0 - 1.0, e.g., 0.15 = 15% drawdown)
    """
    if len(equity_curve) == 0:
        return 0.0

    running_max = np.maximum.accumulate(equity_curve)
    drawdown = (equity_curve - running_max) / running_max

    mdd = float(np.min(drawdown))
    return abs(mdd)


def cagr(equity_curve: np.ndarray, periods_per_year: int = 525600) -> float:
    """
    Calculate CAGR (Compound Annual Growth Rate).

    Args:
        equity_curve: Array of equity values
        periods_per_year: For 1m bars: 525600

    Returns:
        CAGR (annualized)
    """
    if len(equity_curve) < 2:
        return 0.0

    initial_value = equity_curve[0]
    final_value = equity_curve[-1]
    n_periods = len(equity_curve)

    if initial_value <= 0:
        return 0.0

    years = n_periods / periods_per_year
    cagr_value = (final_value / initial_value) ** (1 / years) - 1

    return float(cagr_value)


def hit_rate(positions: np.ndarray, returns: np.ndarray) -> float:
    """
    Calculate Hit Rate (% of profitable trades).

    Args:
        positions: Array of positions (0 = flat, 1 = long)
        returns: Array of returns

    Returns:
        Hit rate (0.0 - 1.0)
    """
    if len(positions) < 2 or len(returns) == 0:
        return 0.0

    # Find position changes (trades)
    position_changes = np.diff(positions)
    trade_entries = np.where(position_changes != 0)[0]

    if len(trade_entries) == 0:
        return 0.0

    # Calculate P&L for each trade
    trade_pnls = []
    for i in range(len(trade_entries) - 1):
        entry_idx = trade_entries[i]
        exit_idx = trade_entries[i + 1]

        if entry_idx < len(returns) and exit_idx <= len(returns):
            trade_return = np.sum(returns[entry_idx:exit_idx])
            trade_pnls.append(trade_return)

    if len(trade_pnls) == 0:
        return 0.0

    winning_trades = sum(1 for pnl in trade_pnls if pnl > 0)
    hit = winning_trades / len(trade_pnls)

    return float(hit)


def turnover(positions: np.ndarray) -> float:
    """
    Calculate Turnover (average position changes per period).

    Args:
        positions: Array of positions

    Returns:
        Turnover (trades per period, annualized for 1m bars)
    """
    if len(positions) < 2:
        return 0.0

    position_changes = np.abs(np.diff(positions))
    avg_turnover = np.mean(position_changes)

    # Annualize (for 1m bars)
    annualized_turnover = avg_turnover * 525600

    return float(annualized_turnover)


def calculate_all_metrics(equity_curve: np.ndarray, positions: np.ndarray) -> dict:
    """
    Calculate all metrics.

    Args:
        equity_curve: Equity curve array
        positions: Position array

    Returns:
        Dict with all metrics
    """
    returns = calculate_returns(equity_curve)

    metrics = {
        "sharpe": sharpe_ratio(returns),
        "sortino": sortino_ratio(returns),
        "mdd": maximum_drawdown(equity_curve),
        "cagr": cagr(equity_curve),
        "hit_rate": hit_rate(positions, returns),
        "turnover": turnover(positions),
        "cum_return": float((equity_curve[-1] / equity_curve[0] - 1) if len(equity_curve) > 0 else 0),
        "final_equity": float(equity_curve[-1]) if len(equity_curve) > 0 else 0,
    }

    return metrics

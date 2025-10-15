"""Test backtest metrics."""
from __future__ import annotations

import numpy as np

from backend.src.backtest.metrics import (
    cagr,
    hit_rate,
    maximum_drawdown,
    sharpe_ratio,
    sortino_ratio,
    turnover,
)


def test_sharpe_ratio():
    """Test Sharpe ratio calculation."""
    # Positive returns
    returns = np.array([0.01, 0.02, -0.005, 0.015, 0.01])
    sharpe = sharpe_ratio(returns, periods_per_year=252)

    assert sharpe > 0, "Sharpe should be positive for positive returns"


def test_sortino_ratio():
    """Test Sortino ratio calculation."""
    returns = np.array([0.01, 0.02, -0.005, 0.015, -0.01])
    sortino = sortino_ratio(returns, periods_per_year=252)

    assert sortino > 0, "Sortino should be positive"


def test_maximum_drawdown():
    """Test MDD calculation."""
    equity = np.array([100, 110, 105, 120, 90, 110])
    mdd = maximum_drawdown(equity)

    # Max drawdown: 120 -> 90 = 25%
    assert abs(mdd - 0.25) < 0.01, f"Expected MDD ~0.25, got {mdd}"


def test_cagr():
    """Test CAGR calculation."""
    # 100 -> 200 over 1 year (252 trading days)
    equity = np.linspace(100, 200, 252)
    cagr_val = cagr(equity, periods_per_year=252)

    # ~100% growth
    assert abs(cagr_val - 1.0) < 0.1, f"Expected CAGR ~1.0, got {cagr_val}"


def test_hit_rate():
    """Test hit rate calculation."""
    # Alternating positions: flat, long, flat, long
    positions = np.array([0, 1, 1, 1, 0, 1, 1, 0])
    returns = np.array([0.01, -0.005, 0.02, 0.01, -0.01, 0.005])

    hit = hit_rate(positions, returns)

    assert 0 <= hit <= 1, "Hit rate should be between 0 and 1"


def test_turnover():
    """Test turnover calculation."""
    positions = np.array([0, 1, 1, 0, 1, 0, 0, 1])
    turn = turnover(positions)

    assert turn > 0, "Turnover should be positive"


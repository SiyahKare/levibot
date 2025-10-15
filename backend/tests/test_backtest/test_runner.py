"""Test backtest runner."""
from __future__ import annotations

import numpy as np
import pandas as pd

from backend.src.backtest.runner_v2 import BacktestRunnerV2, benchmark_buy_and_hold


def test_backtest_runner_basic():
    """Test basic backtest run."""
    # Create sample bars
    n = 100
    bars = pd.DataFrame({
        "ts": pd.date_range("2025-01-01", periods=n, freq="1min").astype(int) // 10**6,
        "open": np.linspace(100, 110, n),
        "high": np.linspace(100, 110, n) * 1.01,
        "low": np.linspace(100, 110, n) * 0.99,
        "close": np.linspace(100, 110, n),
        "volume": np.ones(n) * 1000,
    })

    # Simple signal: always long
    signals = np.ones(n)
    sizes = np.ones(n) * 0.5

    # Run
    runner = BacktestRunnerV2(bars, fee_bps=5, slippage_bps=5, latency_ms=60000)
    results = runner.run(signals, sizes)

    assert len(results["equity_curve"]) == n
    assert results["final_equity"] > 0
    assert len(results["trades"]) > 0


def test_backtest_with_fees():
    """Test that fees are applied."""
    n = 50
    bars = pd.DataFrame({
        "ts": pd.date_range("2025-01-01", periods=n, freq="1min").astype(int) // 10**6,
        "open": np.ones(n) * 100,
        "high": np.ones(n) * 101,
        "low": np.ones(n) * 99,
        "close": np.ones(n) * 100,
        "volume": np.ones(n) * 1000,
    })

    signals = np.ones(n)
    sizes = np.ones(n) * 0.5

    runner = BacktestRunnerV2(bars, fee_bps=10, slippage_bps=0, latency_ms=60000)
    results = runner.run(signals, sizes)

    assert results["total_fees"] > 0, "Fees should be > 0"


def test_benchmark_buy_and_hold():
    """Test buy & hold benchmark."""
    n = 100
    bars = pd.DataFrame({
        "ts": pd.date_range("2025-01-01", periods=n, freq="1min").astype(int) // 10**6,
        "open": np.linspace(100, 120, n),
        "high": np.linspace(100, 120, n) * 1.01,
        "low": np.linspace(100, 120, n) * 0.99,
        "close": np.linspace(100, 120, n),
        "volume": np.ones(n) * 1000,
    })

    results = benchmark_buy_and_hold(bars, initial_capital=10000)

    # Prices go 100 -> 120 = 20% gain
    assert results["final_return"] > 0.15, "B&H should have positive return"


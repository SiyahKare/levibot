"""Smoke tests for backtesting framework."""

import json
import os

import numpy as np
import pandas as pd
from src.backtest.report import save_report
from src.backtest.runner import run_backtest


def dummy_signal(df: pd.DataFrame) -> pd.Series:
    """Simple momentum-based signal for testing."""
    # close mom > 0 → prob_up=0.6, else 0.4
    mom = df["close"].diff().fillna(0.0)
    return (mom > 0).astype(float) * 0.2 + 0.4


def test_backtest_runner():
    """Test backtest runner with synthetic data."""
    # 2 days of minute bars (2880 bars)
    ts0 = 1_700_000_000_000
    ts = np.arange(ts0, ts0 + 60_000 * 2880, 60_000)
    close = np.linspace(100, 105, len(ts))

    bars = pd.DataFrame(
        {
            "ts": ts,
            "open": close,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "volume": 1000,
        }
    )

    res = run_backtest(bars, dummy_signal, fee_bps=5, slippage_bps=5)

    # Validate structure
    assert "metrics" in res
    assert "equity" in res
    assert "pnl" in res
    assert "side" in res
    assert "prob" in res

    # Validate metrics
    m = res["metrics"]
    assert "sharpe" in m
    assert "sortino" in m
    assert "max_drawdown" in m
    assert "hitrate" in m
    assert "turnover" in m
    assert "cum_return_pct" in m
    assert "n_minutes" in m
    assert "n_trades" in m

    # Validate arrays
    assert len(res["equity"]) == len(bars)
    assert len(res["pnl"]) == len(bars)
    assert len(res["side"]) == len(bars)
    assert len(res["prob"]) == len(bars)


def test_backtest_report(tmp_path):
    """Test report generation and artifact saving."""
    # 1 day of minute bars (1440 bars)
    ts0 = 1_700_000_000_000
    ts = np.arange(ts0, ts0 + 60_000 * 1440, 60_000)
    close = np.linspace(100, 103, len(ts))

    bars = pd.DataFrame(
        {
            "ts": ts,
            "open": close,
            "high": close + 0.2,
            "low": close - 0.2,
            "close": close,
            "volume": 1000,
        }
    )

    res = run_backtest(bars, dummy_signal, fee_bps=5, slippage_bps=5)
    out = save_report(res, "BTCUSDT", out_dir=str(tmp_path / "reports"))

    # Validate output files
    assert os.path.exists(out["markdown"])
    assert os.path.exists(out["metrics"])
    assert os.path.exists(out["equity"])

    # Validate Markdown content
    md_content = open(out["markdown"]).read()
    assert "Backtest Report — BTCUSDT" in md_content
    assert "Sharpe" in md_content
    assert "Max Drawdown" in md_content

    # Validate JSON metrics
    metrics = json.loads(open(out["metrics"]).read())
    assert "sharpe" in metrics
    assert "n_trades" in metrics

    # Validate equity numpy array
    equity = np.load(out["equity"])
    assert len(equity) == len(bars)
    assert equity.dtype == np.float64


"""Backtest report generation (Markdown, JSON, artifacts)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def to_markdown(result: dict[str, Any], symbol: str) -> str:
    """
    Generate Markdown summary report from backtest results.

    Args:
        result: Backtest result dict (from run_backtest)
        symbol: Trading symbol (e.g., "BTCUSDT")

    Returns:
        Markdown-formatted report string
    """
    m = result["metrics"]
    tbl = (
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Sharpe | {m['sharpe']:.2f} |\n"
        f"| Sortino | {m['sortino']:.2f} |\n"
        f"| Max Drawdown | {m['max_drawdown']:.2%} |\n"
        f"| Hit Rate | {m['hitrate']:.2%} |\n"
        f"| Turnover | {m['turnover']:.2f} |\n"
        f"| Cum Return | {m['cum_return_pct']:.2f}% |\n"
        f"| Minutes | {m['n_minutes']} |\n"
        f"| Trades | {m['n_trades']} |\n"
    )
    return f"# Backtest Report — {symbol}\n\n{tbl}\n"


def save_report(
    result: dict[str, Any], symbol: str, out_dir: str = "reports/backtests"
) -> dict[str, str]:
    """
    Save backtest report artifacts (Markdown, JSON, equity curve).

    Args:
        result: Backtest result dict
        symbol: Trading symbol
        out_dir: Output directory path

    Returns:
        Dictionary with paths to saved files
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    # Markdown summary
    md = to_markdown(result, symbol)
    md_path = Path(out_dir) / f"{symbol}_summary.md"
    md_path.write_text(md)

    # Equity curve (binary numpy array)
    equity_path = Path(out_dir) / f"{symbol}_equity.npy"
    np.save(equity_path, result["equity"].astype("float64"))

    # Metrics JSON
    metrics_path = Path(out_dir) / f"{symbol}_metrics.json"
    metrics_path.write_text(json.dumps(result["metrics"], indent=2))

    return {
        "markdown": str(md_path),
        "metrics": str(metrics_path),
        "equity": str(equity_path),
    }


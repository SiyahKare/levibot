"""Backtesting framework for vectorized strategy simulation."""

from .metrics import hitrate, max_drawdown, sharpe, sortino, turnover
from .report import save_report, to_markdown
from .runner import run_backtest

__all__ = [
    "run_backtest",
    "sharpe",
    "sortino",
    "max_drawdown",
    "hitrate",
    "turnover",
    "to_markdown",
    "save_report",
]


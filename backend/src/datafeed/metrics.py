from __future__ import annotations

from typing import List
import polars as pl


def fetch_funding_placeholder(symbol: str, limit: int = 1000) -> pl.DataFrame:
    """Synthetic funding rate series for pipelines/backtests."""
    vals = []
    for i in range(limit):
        vals.append({"ts": i, "symbol": symbol, "funding": 0.0001 * ((i % 20) - 10) / 10.0})
    return pl.DataFrame(vals)


def fetch_open_interest_placeholder(symbol: str, limit: int = 1000) -> pl.DataFrame:
    vals = []
    base = 1_000_000.0
    for i in range(limit):
        vals.append({"ts": i, "symbol": symbol, "oi": base * (1.0 + 0.05 * ((i % 50) / 50.0))})
    return pl.DataFrame(vals)



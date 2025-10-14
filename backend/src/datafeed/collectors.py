from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass
class Kline:
    ts: int
    open: float
    high: float
    low: float
    close: float
    volume: float


def klines_to_df(klines: list[Kline]) -> pl.DataFrame:
    return pl.DataFrame([k.__dict__ for k in klines])


def fetch_ohlcv_placeholder(
    symbol: str, timeframe: str = "1m", limit: int = 2000
) -> pl.DataFrame:
    # Placeholder: create a synthetic price series for testing pipelines
    import math

    data: list[Kline] = []
    price = 100.0
    for i in range(limit):
        price *= 1.0 + 0.001 * math.sin(i / 20.0)
        high = price * 1.001
        low = price * 0.999
        data.append(
            Kline(ts=i, open=price, high=high, low=low, close=price, volume=1000.0)
        )
    return klines_to_df(data)

from __future__ import annotations

import polars as pl


def add_basic_features(df: pl.DataFrame) -> pl.DataFrame:
    close = df.get_column("close")
    ema_fast = close.ewm_mean(span=21).alias("ema_fast")
    ema_slow = close.ewm_mean(span=55).alias("ema_slow")
    rsi = (close - close.shift(1)).fill_null(0).cumsum().alias("rsi_proxy")
    out = df.with_columns([ema_fast, ema_slow, rsi])
    return out



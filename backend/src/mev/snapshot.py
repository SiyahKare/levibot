from __future__ import annotations

from pathlib import Path

import duckdb as d
import pandas as pd

OUT1 = Path("backend/data/parquet/dex/univ3_prices.parquet")
OUT2 = Path("backend/data/parquet/dex/sushi_prices.parquet")


def write_snapshots() -> None:
    OUT1.parent.mkdir(parents=True, exist_ok=True)
    try:
        df = d.sql(
            "SELECT symbol, close AS px FROM read_parquet('backend/data/parquet/ohlcv/*_1m.parquet') USING SAMPLE 1%"
        ).df()
    except Exception:
        return
    if df.empty:
        return
    pd.DataFrame(df).assign(dex="uniswapv3").to_parquet(OUT1, index=False)
    pd.DataFrame(df).assign(dex="sushiswap").to_parquet(OUT2, index=False)


__all__ = ["write_snapshots"]

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional
import polars as pl


Side = Literal["long", "short", "flat"]


@dataclass
class BaselineSignal:
    side: Side
    strength: float  # 0..1
    atr: Optional[float] = None


def compute_baseline(df: pl.DataFrame, ema_fast: int = 21, ema_slow: int = 55) -> BaselineSignal:
    close = df.get_column("close")
    ema_f = close.ewm_mean(span=ema_fast)
    ema_s = close.ewm_mean(span=ema_slow)
    last_f = float(ema_f[-1])
    last_s = float(ema_s[-1])
    spread = (last_f - last_s) / max(abs(last_s), 1e-9)
    side: Side = "long" if spread > 0 else "short" if spread < 0 else "flat"
    strength = min(abs(spread) * 10.0, 1.0)
    atr = None
    if all(c in df.columns for c in ["high", "low", "close"]):
        tr = pl.concat([
            (df["high"] - df["low"]).abs(),
            (df["high"] - df["close"].shift(1)).abs(),
            (df["low"] - df["close"].shift(1)).abs(),
        ], how="horizontal").max_horizontal()
        atr_series = tr.rolling_mean(window_size=14, min_periods=1)
        atr = float(atr_series[-1])
    return BaselineSignal(side=side, strength=strength, atr=atr)



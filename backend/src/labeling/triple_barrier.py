from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass
class TBParams:
    pt_mult: float = 3.0
    sl_mult: float = 2.0
    horizon_bars: int = 60


def label_triple_barrier(
    df: pl.DataFrame, atr_col: str = "atr", params: TBParams | None = None
) -> pl.Series:
    p = params or TBParams()
    close = df.get_column("close")
    atr = df.get_column(atr_col) if atr_col in df.columns else close.rolling_std(14)
    labels = []
    n = len(close)
    for i in range(n):
        entry = float(close[i])
        pt = entry * (1.0 + (atr[i] * p.pt_mult) / max(entry, 1e-9))
        sl = entry * (1.0 - (atr[i] * p.sl_mult) / max(entry, 1e-9))
        label = 0
        for j in range(i + 1, min(n, i + p.horizon_bars)):
            c = float(close[j])
            if c >= pt:
                label = 1
                break
            if c <= sl:
                label = -1
                break
        labels.append(label)
    return pl.Series(labels)

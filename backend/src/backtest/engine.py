from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import polars as pl


@dataclass
class BTResult:
    equity_curve: pl.DataFrame
    trades: pl.DataFrame
    metrics: dict[str, float]


class WalkForwardBacktester:
    def __init__(self, fee_bps: float = 7.0, slippage_bps: float = 2.0) -> None:
        self.fee = fee_bps / 10000.0
        self.slip = slippage_bps / 10000.0

    def run(
        self,
        ohlcv: pl.DataFrame,
        signal_fn: Callable[[pl.DataFrame], dict[str, float]],
        initial_equity: float = 10_000.0,
    ) -> BTResult:
        equity = initial_equity
        curve = []
        trades = []
        close = ohlcv.get_column("close")
        for i in range(1, len(close)):
            window = ohlcv.slice(0, i + 1)
            sig = signal_fn(window)
            pnl = 0.0
            if sig.get("side") == "long":
                pnl = float((close[i] / close[i - 1]) - 1.0)
            elif sig.get("side") == "short":
                pnl = float((close[i - 1] / close[i]) - 1.0)
            pnl -= self.fee + self.slip
            equity *= 1.0 + pnl
            curve.append({"idx": i, "equity": equity})
            if sig.get("side") in ("long", "short"):
                trades.append({"i": i, "side": sig.get("side"), "ret": pnl})

        curve_df = pl.DataFrame(curve)
        trades_df = pl.DataFrame(trades)
        metrics = {
            "final_equity": float(equity),
            "trades": float(len(trades)),
            "avg_trade": float(trades_df["ret"].mean() if len(trades) else 0.0),
        }
        return BTResult(equity_curve=curve_df, trades=trades_df, metrics=metrics)

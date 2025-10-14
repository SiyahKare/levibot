"""
LSE Strategy Configuration
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class StrategyConfig:
    """LSE Configuration"""

    symbol: str = "BTCUSDT"
    mode: Literal["paper", "real"] = "paper"
    leverage: int = 3
    quote_budget: float = 1000.0
    windows: list[int] = field(default_factory=lambda: [3, 15, 60])
    atr: dict = field(default_factory=lambda: {"period": 14, "k_enter": 0.8})
    zscore: dict = field(default_factory=lambda: {"lookback": 120, "z_enter": 1.5})
    risk: dict = field(
        default_factory=lambda: {
            "max_daily_dd": 0.02,
            "max_open_trades": 1,
            "slippage_bps": 1.5,
            "fee_bps": 7,
            "hard_stop_bps": 15,
            "take_profit_bps": 25,
        }
    )
    filters: dict = field(
        default_factory=lambda: {
            "min_vol_bps": 5,
            "max_spread_bps": 1,
            "max_latency_ms": 120,
        }
    )
    recording: dict = field(
        default_factory=lambda: {"parquet": False, "path": "data/lse/"}
    )

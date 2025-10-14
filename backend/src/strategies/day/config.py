"""
Daytrade Engine Configuration
Intraday momentum strategy (5m-15m timeframe)
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class StrategyConfig:
    """Daytrade engine configuration"""

    symbol: str = "BTCUSDT"
    mode: Literal["paper", "real"] = "paper"
    leverage: int = 2
    quote_budget: float = 1000.0
    base_tf: str = "5m"  # Base timeframe
    ema_fast: int = 20
    ema_slow: int = 50
    donchian_period: int = 20
    rsi_period: int = 14
    risk: dict = field(
        default_factory=lambda: {
            "max_daily_dd": 0.03,
            "max_open_trades": 2,
            "slippage_bps": 1.0,
            "fee_bps": 7,
            "hard_stop_bps": 20,
            "take_profit_bps": 35,
            "rr_min": 1.3,
        }
    )
    filters: dict = field(
        default_factory=lambda: {
            "min_vol_bps": 10,
            "max_spread_bps": 1.5,
            "max_latency_ms": 150,
        }
    )
    recording: dict = field(
        default_factory=lambda: {"parquet": False, "path": "data/day/"}
    )

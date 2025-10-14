"""
Swing Engine Configuration
Multi-day position trading (4H-1D timeframe)
"""
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class StrategyConfig:
    """Swing engine configuration"""

    symbol: str = "BTCUSDT"
    mode: Literal["paper", "real"] = "paper"
    leverage: int = 1  # Conservative for swing
    quote_budget: float = 2000.0
    base_tf: str = "4h"  # Base timeframe
    ema_fast: int = 21
    ema_slow: int = 55
    donchian_period: int = 20
    rsi_period: int = 14
    atr_period: int = 14
    atr_stop_mult: float = 2.5
    adx_period: int = 14
    min_adx: float = 20.0
    risk: dict = field(
        default_factory=lambda: {
            "max_daily_dd": 0.05,
            "max_open_trades": 1,
            "slippage_bps": 0.5,
            "fee_bps": 7,
            "hard_stop_bps": 30,
            "take_profit_bps": 60,
            "rr_min": 1.5,
        }
    )
    filters: dict = field(
        default_factory=lambda: {
            "min_vol_bps": 15,
            "max_spread_bps": 2.0,
            "max_latency_ms": 200,
        }
    )
    recording: dict = field(
        default_factory=lambda: {"parquet": False, "path": "data/swing/"}
    )


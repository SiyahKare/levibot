"""
RSI + MACD Strategy Configuration
"""
from dataclasses import dataclass
from typing import Literal


@dataclass
class RsiConfig:
    """RSI parameters"""
    period: int = 14
    enter_above: float = 50.0
    pullback_zone: tuple[float, float] = (40.0, 45.0)


@dataclass
class MacdConfig:
    """MACD parameters"""
    fast: int = 12
    slow: int = 26
    signal: int = 9


@dataclass
class RiskConfig:
    """Risk management parameters"""
    atr_period: int = 14
    sl_atr_mult: float = 1.5
    tp_atr_mult: float = 2.0
    timeout_bars: int = 30
    fee_bps: float = 7.0


@dataclass
class FiltersConfig:
    """Entry filters"""
    max_spread_bps: float = 1.0
    max_latency_ms: float = 150.0
    min_vol_bps_60s: float = 5.0
    min_adx: float | None = None  # Optional, for swing only


@dataclass
class SizingConfig:
    """Position sizing"""
    quote_budget: float | None = None  # Fixed USD amount
    r_per_trade: float | None = None   # % of account risk
    max_concurrent: int = 1


@dataclass
class RsiMacdConfig:
    """
    Complete RSI + MACD strategy configuration.
    
    Supports three modes:
      - scalp: 1m, tight stops, high frequency
      - day: 15m, moderate targets, medium frequency
      - swing: 4h, wide targets, low frequency
    """
    name: str = "rsi_macd"
    mode: Literal["scalp", "day", "swing"] = "day"
    symbol: str = "BTCUSDT"
    tf: str = "15m"
    
    rsi: RsiConfig = None
    macd: MacdConfig = None
    risk: RiskConfig = None
    filters: FiltersConfig = None
    sizing: SizingConfig = None
    
    sync_bars: int = 3
    cooldown_bars: int = 5
    partial_take_profits: list[float] | None = None
    
    def __post_init__(self):
        """Initialize nested configs with defaults if not provided"""
        if self.rsi is None:
            self.rsi = RsiConfig()
        if self.macd is None:
            self.macd = MacdConfig()
        if self.risk is None:
            self.risk = RiskConfig()
        if self.filters is None:
            self.filters = FiltersConfig()
        if self.sizing is None:
            self.sizing = SizingConfig()
    
    @classmethod
    def from_dict(cls, data: dict) -> "RsiMacdConfig":
        """Load config from dictionary (YAML load)"""
        rsi_data = data.get("rsi", {})
        macd_data = data.get("macd", {})
        risk_data = data.get("risk", {})
        filters_data = data.get("filters", {})
        sizing_data = data.get("sizing", {})
        
        return cls(
            name=data.get("name", "rsi_macd"),
            mode=data.get("mode", "day"),
            symbol=data.get("symbol", "BTCUSDT"),
            tf=data.get("tf", "15m"),
            rsi=RsiConfig(
                period=rsi_data.get("period", 14),
                enter_above=rsi_data.get("enter_above", 50.0),
                pullback_zone=tuple(rsi_data.get("pullback_zone", [40.0, 45.0]))
            ),
            macd=MacdConfig(
                fast=macd_data.get("fast", 12),
                slow=macd_data.get("slow", 26),
                signal=macd_data.get("signal", 9)
            ),
            risk=RiskConfig(
                atr_period=risk_data.get("atr_period", 14),
                sl_atr_mult=risk_data.get("sl_atr_mult", 1.5),
                tp_atr_mult=risk_data.get("tp_atr_mult", 2.0),
                timeout_bars=risk_data.get("timeout_bars", 30),
                fee_bps=risk_data.get("fee_bps", 7.0)
            ),
            filters=FiltersConfig(
                max_spread_bps=filters_data.get("max_spread_bps", 1.0),
                max_latency_ms=filters_data.get("max_latency_ms", 150.0),
                min_vol_bps_60s=filters_data.get("min_vol_bps_60s", 5.0),
                min_adx=filters_data.get("min_adx")
            ),
            sizing=SizingConfig(
                quote_budget=sizing_data.get("quote_budget"),
                r_per_trade=sizing_data.get("r_per_trade"),
                max_concurrent=sizing_data.get("max_concurrent", 1)
            ),
            sync_bars=data.get("sync_bars", 3),
            cooldown_bars=data.get("cooldown_bars", 5),
            partial_take_profits=data.get("partial_take_profits")
        )
    
    def to_dict(self) -> dict:
        """Export config to dictionary"""
        return {
            "name": self.name,
            "mode": self.mode,
            "symbol": self.symbol,
            "tf": self.tf,
            "rsi": {
                "period": self.rsi.period,
                "enter_above": self.rsi.enter_above,
                "pullback_zone": list(self.rsi.pullback_zone)
            },
            "macd": {
                "fast": self.macd.fast,
                "slow": self.macd.slow,
                "signal": self.macd.signal
            },
            "risk": {
                "atr_period": self.risk.atr_period,
                "sl_atr_mult": self.risk.sl_atr_mult,
                "tp_atr_mult": self.risk.tp_atr_mult,
                "timeout_bars": self.risk.timeout_bars,
                "fee_bps": self.risk.fee_bps
            },
            "filters": {
                "max_spread_bps": self.filters.max_spread_bps,
                "max_latency_ms": self.filters.max_latency_ms,
                "min_vol_bps_60s": self.filters.min_vol_bps_60s,
                "min_adx": self.filters.min_adx
            },
            "sizing": {
                "quote_budget": self.sizing.quote_budget,
                "r_per_trade": self.sizing.r_per_trade,
                "max_concurrent": self.sizing.max_concurrent
            },
            "sync_bars": self.sync_bars,
            "cooldown_bars": self.cooldown_bars,
            "partial_take_profits": self.partial_take_profits
        }



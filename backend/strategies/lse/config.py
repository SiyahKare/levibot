"""
LSE Configuration
Strategy parameters and configuration
"""
from dataclasses import dataclass


@dataclass
class LSEConfig:
    """LSE Strategy Configuration"""
    
    # Symbol & Mode
    symbol: str = "BTCUSDT"
    mode: str = "paper"  # paper | real
    
    # Position Sizing
    quote_budget: float = 500.0  # USD per trade
    max_open_trades: int = 1
    
    # Entry Conditions
    confidence_min: float = 0.60
    atr_k: float = 1.5  # ATR threshold multiplier
    vol_zscore_min: float = 1.0  # Realized vol z-score
    
    # Exit Conditions
    take_profit_bps: float = 15.0  # basis points
    hard_stop_bps: float = 30.0
    timeout_bars: int = 20  # Exit after N bars if not TP/SL
    
    # Guards
    spread_max_bps: float = 5.0
    latency_max_ms: float = 50.0
    fee_bps: float = 7.0  # Taker fee
    slippage_bps: float = 2.0
    
    # Features
    atr_period: int = 14
    vol_window: int = 50
    zscore_window: int = 100
    
    # Risk
    max_dd_pct: float = 5.0  # Daily drawdown limit
    kill_switch: bool = False
    
    def __post_init__(self):
        """Validate configuration"""
        if self.confidence_min < 0.5 or self.confidence_min > 1.0:
            raise ValueError("confidence_min must be between 0.5 and 1.0")
        
        if self.quote_budget <= 0:
            raise ValueError("quote_budget must be positive")
        
        if self.take_profit_bps <= 0 or self.hard_stop_bps <= 0:
            raise ValueError("TP and SL must be positive")
        
        if self.hard_stop_bps < self.take_profit_bps:
            raise ValueError("hard_stop_bps should be >= take_profit_bps for R:R")
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "mode": self.mode,
            "quote_budget": self.quote_budget,
            "max_open_trades": self.max_open_trades,
            "confidence_min": self.confidence_min,
            "atr_k": self.atr_k,
            "vol_zscore_min": self.vol_zscore_min,
            "take_profit_bps": self.take_profit_bps,
            "hard_stop_bps": self.hard_stop_bps,
            "timeout_bars": self.timeout_bars,
            "spread_max_bps": self.spread_max_bps,
            "latency_max_ms": self.latency_max_ms,
            "fee_bps": self.fee_bps,
            "slippage_bps": self.slippage_bps,
            "atr_period": self.atr_period,
            "vol_window": self.vol_window,
            "zscore_window": self.zscore_window,
            "max_dd_pct": self.max_dd_pct,
            "kill_switch": self.kill_switch,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "LSEConfig":
        """Create from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


"""Genetic Algorithm chromosome definition and random generation."""

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class Chromosome:
    """Trading strategy chromosome with all parameters."""

    # Model parameters
    model_type: int  # 0=logreg, 1=rf
    rf_n_estimators: int
    rf_max_depth: int
    lr_C: float

    # Technical indicators
    rsi_len: int
    rsi_buy: int
    rsi_sell: int
    ema_fast: int
    ema_slow: int

    # Risk management
    tp_bps: int  # Take profit basis points
    sl_bps: int  # Stop loss basis points
    hold_bars: int  # Maximum hold period
    risk_bps: int  # Risk per trade

    # Portfolio management
    regime_filter: int  # 0/1 - trend filter
    vol_target_pct: int  # 10..30 - volatility target
    max_leverage: int  # 1..3 - maximum leverage

    # Label generation (triple barrier)
    tb_u_bps: int  # Triple barrier up
    tb_d_bps: int  # Triple barrier down
    tb_t_bars: int  # Triple barrier time limit

    def to_dict(self) -> dict[str, Any]:
        """Convert chromosome to dictionary."""
        return {
            "model_type": self.model_type,
            "rf_n_estimators": self.rf_n_estimators,
            "rf_max_depth": self.rf_max_depth,
            "lr_C": self.lr_C,
            "rsi_len": self.rsi_len,
            "rsi_buy": self.rsi_buy,
            "rsi_sell": self.rsi_sell,
            "ema_fast": self.ema_fast,
            "ema_slow": self.ema_slow,
            "tp_bps": self.tp_bps,
            "sl_bps": self.sl_bps,
            "hold_bars": self.hold_bars,
            "risk_bps": self.risk_bps,
            "regime_filter": self.regime_filter,
            "vol_target_pct": self.vol_target_pct,
            "max_leverage": self.max_leverage,
            "tb_u_bps": self.tb_u_bps,
            "tb_d_bps": self.tb_d_bps,
            "tb_t_bars": self.tb_t_bars,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Chromosome":
        """Create chromosome from dictionary."""
        return cls(**data)


def random_chrom() -> Chromosome:
    """Generate random chromosome within valid ranges."""
    return Chromosome(
        # Model parameters
        model_type=random.choice([0, 1]),
        rf_n_estimators=random.randint(50, 300),
        rf_max_depth=random.randint(2, 10),
        lr_C=10 ** random.uniform(-3, 1),
        # Technical indicators
        rsi_len=random.randint(7, 21),
        rsi_buy=random.randint(20, 40),
        rsi_sell=random.randint(60, 80),
        ema_fast=random.randint(8, 50),
        ema_slow=random.randint(60, 200),
        # Risk management
        tp_bps=random.randint(15, 120),
        sl_bps=random.randint(10, 80),
        hold_bars=random.randint(20, 300),
        risk_bps=random.randint(10, 50),
        # Portfolio management
        regime_filter=random.choice([0, 1]),
        vol_target_pct=random.choice([10, 15, 20, 25, 30]),
        max_leverage=random.choice([1, 2, 3]),
        # Label generation
        tb_u_bps=random.randint(30, 120),
        tb_d_bps=random.randint(30, 120),
        tb_t_bars=random.randint(20, 240),
    )


def validate_chromosome(chrom: Chromosome) -> bool:
    """Validate chromosome parameters are within bounds."""
    try:
        # Model validation
        assert chrom.model_type in [0, 1]
        assert 20 <= chrom.rf_n_estimators <= 500
        assert 2 <= chrom.rf_max_depth <= 15
        assert 0.001 <= chrom.lr_C <= 10.0

        # Technical indicators
        assert 5 <= chrom.rsi_len <= 30
        assert 10 <= chrom.rsi_buy <= 50
        assert 50 <= chrom.rsi_sell <= 90
        assert chrom.rsi_buy < chrom.rsi_sell
        assert 5 <= chrom.ema_fast <= 100
        assert 50 <= chrom.ema_slow <= 300
        assert chrom.ema_fast < chrom.ema_slow

        # Risk management
        assert 5 <= chrom.tp_bps <= 200
        assert 5 <= chrom.sl_bps <= 150
        assert 10 <= chrom.hold_bars <= 500
        assert 5 <= chrom.risk_bps <= 100

        # Portfolio management
        assert chrom.regime_filter in [0, 1]
        assert 5 <= chrom.vol_target_pct <= 50
        assert 1 <= chrom.max_leverage <= 5

        # Label generation
        assert 10 <= chrom.tb_u_bps <= 200
        assert 10 <= chrom.tb_d_bps <= 200
        assert 10 <= chrom.tb_t_bars <= 500

        return True
    except AssertionError:
        return False

"""
Risk manager: equity tracking, position sizing, global guards.
"""

import time
from dataclasses import dataclass, field

from .policy import RiskPolicy, load_policy


@dataclass
class SymbolState:
    """
    Per-symbol state tracking.
    """
    open_position: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl_today: float = 0.0
    last_trade_ts: float = 0.0


@dataclass
class EquityBook:
    """
    Equity and PnL tracking.
    """
    equity_start_day: float = 10000.0
    equity_now: float = 10000.0
    day_start_ts: float = field(default_factory=lambda: time.time())


class RiskManager:
    """
    Risk management system.
    
    Features:
    - Equity and daily PnL tracking
    - Position sizing (volatility + Kelly + confidence)
    - Global stop loss (max daily loss)
    - Per-symbol risk limits
    - Concurrent position limits
    
    Integration:
    - Engine calls can_open_new_position() before trading
    - Engine calls calc_position_size() for sizing
    - Engine calls on_order_filled() / on_position_closed() for tracking
    """
    
    def __init__(self, policy: RiskPolicy | None = None, base_equity: float = 10000.0):
        """
        Args:
            policy: Risk policy (defaults to loaded from YAML)
            base_equity: Starting equity
        """
        self.policy = policy or load_policy()
        self.book = EquityBook(
            equity_start_day=base_equity,
            equity_now=base_equity
        )
        self.symbols: dict[str, SymbolState] = {}
        self._positions_open = 0
    
    # ========== Equity & PnL Lifecycle ==========
    
    def on_day_reset(self) -> None:
        """
        Reset daily tracking.
        
        Call this at start of each trading day.
        """
        self.book.equity_start_day = self.book.equity_now
        self.book.day_start_ts = time.time()
        
        for state in self.symbols.values():
            state.realized_pnl_today = 0.0
    
    def update_equity(
        self,
        realized_delta: float = 0.0,
        unrealized_by_symbol: dict[str, float] | None = None
    ) -> None:
        """
        Update equity with realized/unrealized PnL.
        
        Args:
            realized_delta: Realized PnL change
            unrealized_by_symbol: Unrealized PnL by symbol
        """
        # Realized PnL
        self.book.equity_now += realized_delta
        
        # Unrealized PnL
        if unrealized_by_symbol:
            for symbol, pnl in unrealized_by_symbol.items():
                state = self.symbols.setdefault(symbol, SymbolState())
                state.unrealized_pnl = pnl
    
    def realized_today_pct(self) -> float:
        """
        Get realized PnL today as percentage.
        
        Returns:
            Percentage (-100 to +inf)
        """
        day_pnl = self.book.equity_now - self.book.equity_start_day
        return 100.0 * day_pnl / max(1e-9, self.book.equity_start_day)
    
    def is_global_stop(self) -> bool:
        """
        Check if global stop loss is triggered.
        
        Returns:
            True if daily loss exceeds max_daily_loss_pct
        """
        return self.realized_today_pct() <= -abs(self.policy.max_daily_loss_pct)
    
    # ========== Position Sizing ==========
    
    @staticmethod
    def _vol_position_scale(vol_annual: float, vol_target_ann: float) -> float:
        """
        Volatility-based position scaling.
        
        Scale = target_vol / actual_vol
        
        Args:
            vol_annual: Actual annual volatility (e.g., 0.8)
            vol_target_ann: Target annual volatility (e.g., 0.15)
        
        Returns:
            Position scale factor (0.05 to 1.5)
        """
        if vol_annual <= 0:
            return 0.5
        
        scale = vol_target_ann / vol_annual
        return max(0.05, min(1.5, scale))
    
    @staticmethod
    def _kelly_size(prob_up: float, risk_reward: float = 1.0) -> float:
        """
        Kelly criterion sizing.
        
        Formula: f* = p - (1-p)/R
        
        Args:
            prob_up: Probability of winning (0-1)
            risk_reward: Risk/reward ratio
        
        Returns:
            Kelly fraction (0-1)
        """
        p = max(0.0, min(1.0, prob_up))
        f = p - (1 - p) / max(1e-9, risk_reward)
        return max(0.0, min(1.0, f))
    
    def calc_position_size(
        self,
        symbol: str,
        prob_up: float,
        confidence: float,
        vol_annual: float
    ) -> float:
        """
        Calculate position size as fraction of equity.
        
        Combines:
        - Kelly criterion (edge-based)
        - Volatility targeting (risk-based)
        - Confidence scaling (ML certainty)
        
        Args:
            symbol: Trading symbol
            prob_up: Probability of price increase (0-1)
            confidence: ML model confidence (0-1)
            vol_annual: Annual volatility (e.g., 0.6)
        
        Returns:
            Position size as fraction of equity (0 to max_symbol_risk_pct)
        """
        # Kelly sizing
        kelly = self._kelly_size(prob_up, risk_reward=1.2)
        kelly_scaled = kelly * self.policy.kelly_fraction
        
        # Volatility targeting
        vol_scale = self._vol_position_scale(vol_annual, self.policy.vol_target_ann)
        
        # Confidence scaling
        conf_scale = 0.5 + 0.5 * max(0.0, min(1.0, confidence))
        
        # Combined size
        raw_size = kelly_scaled * vol_scale * conf_scale
        
        # Apply per-symbol cap
        final_size = min(self.policy.max_symbol_risk_pct, raw_size)
        
        return final_size
    
    # ========== Guards & Checks ==========
    
    def can_open_new_position(self, symbol: str) -> bool:
        """
        Check if new position can be opened.
        
        Checks:
        - Global stop loss
        - Concurrent position limit
        
        Args:
            symbol: Trading symbol
        
        Returns:
            True if position can be opened
        """
        # Global stop check
        if self.is_global_stop():
            return False
        
        # Concurrent positions check
        if self._positions_open >= self.policy.max_concurrent_positions:
            return False
        
        # TODO: Add symbol-specific checks (cooldown, etc.)
        
        return True
    
    # ========== Event Tracking ==========
    
    def on_order_filled(
        self,
        symbol: str,
        side: str,
        notional: float,
        realized_pnl: float = 0.0
    ) -> None:
        """
        Track order fill event.
        
        Args:
            symbol: Trading symbol
            side: Order side ("long" or "short")
            notional: Position notional value
            realized_pnl: Realized PnL (if closing)
        """
        state = self.symbols.setdefault(symbol, SymbolState())
        state.last_trade_ts = time.time()
        
        # Track position opening
        if side in ("long", "short"):
            self._positions_open = min(self._positions_open + 1, 10**6)
        
        # Track realized PnL
        if realized_pnl != 0.0:
            self.book.equity_now += realized_pnl
            state.realized_pnl_today += realized_pnl
    
    def on_position_closed(self, symbol: str, realized_pnl: float) -> None:
        """
        Track position close event.
        
        Args:
            symbol: Trading symbol
            realized_pnl: Realized PnL
        """
        state = self.symbols.setdefault(symbol, SymbolState())
        state.last_trade_ts = time.time()
        
        # Update position count
        self._positions_open = max(0, self._positions_open - 1)
        
        # Update equity
        self.book.equity_now += realized_pnl
        state.realized_pnl_today += realized_pnl
    
    # ========== Inspection ==========
    
    def summary(self) -> dict:
        """
        Get risk manager summary.
        
        Returns:
            Summary dictionary
        """
        return {
            "equity_now": round(self.book.equity_now, 2),
            "equity_start_day": round(self.book.equity_start_day, 2),
            "realized_today_pct": round(self.realized_today_pct(), 2),
            "positions_open": self._positions_open,
            "global_stop": self.is_global_stop(),
            "policy": {
                "max_daily_loss_pct": self.policy.max_daily_loss_pct,
                "max_symbol_risk_pct": self.policy.max_symbol_risk_pct,
                "kelly_fraction": self.policy.kelly_fraction,
                "vol_target_ann": self.policy.vol_target_ann,
                "max_concurrent_positions": self.policy.max_concurrent_positions,
            },
        }


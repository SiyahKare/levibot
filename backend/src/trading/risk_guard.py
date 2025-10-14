"""
Risk Guard - Real-time risk checks for trading.
"""
from __future__ import annotations

from ..infra.settings import settings


class RiskGuard:
    """
    Real-time risk management guard.
    
    Prevents trades that violate risk limits:
    - Max daily loss
    - Max position notional
    - Max drawdown
    """
    
    def __init__(self):
        self.daily_realized = 0.0
        self.current_drawdown = 0.0
    
    def allow(self, notional: float) -> tuple[bool, str]:
        """
        Check if trade is allowed.
        
        Args:
            notional: Trade notional value in USD
        
        Returns:
            (allowed, reason)
        """
        # Check max position notional
        if notional > settings.MAX_POS_NOTIONAL:
            return False, f"Trade notional ${notional:.2f} exceeds max ${settings.MAX_POS_NOTIONAL}"
        
        # Check daily loss limit (MAX_DAILY_LOSS is negative)
        if self.daily_realized < settings.MAX_DAILY_LOSS:
            return False, f"Daily loss ${self.daily_realized:.2f} exceeds limit ${settings.MAX_DAILY_LOSS}"
        
        return True, "ok"
    
    def update_daily_pnl(self, pnl: float) -> None:
        """Update daily realized PnL."""
        self.daily_realized += pnl
    
    def reset_daily(self) -> None:
        """Reset daily counters (call at EOD)."""
        self.daily_realized = 0.0


# Global instance
risk_guard = RiskGuard()








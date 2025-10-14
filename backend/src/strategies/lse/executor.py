"""
LSE Executor - Trade execution via paper portfolio
"""
import time
from typing import Literal

from ...exec.paper_portfolio import get_paper_portfolio


class LSEExecutor:
    """
    LSE trade executor with paper portfolio integration.
    
    Handles:
    - Position entry/exit
    - Stop loss / Take profit
    - PnL tracking
    """
    
    def __init__(self, symbol: str, mode: Literal["paper", "real"] = "paper"):
        self.symbol = symbol
        self.mode = mode
        self._portfolio = get_paper_portfolio() if mode == "paper" else None
        self._position_id = None
    
    def has_position(self) -> bool:
        """Check if there's an open position for this symbol."""
        if self.mode == "paper" and self._portfolio:
            return self.symbol in self._portfolio.positions
        return False
    
    def enter_long(self, price: float, qty: float, reason: str = "signal") -> dict:
        """
        Enter long position.
        
        Args:
            price: Entry price
            qty: Quantity (in base asset)
            reason: Entry reason (for logging)
        
        Returns:
            Trade result dict
        """
        if self.mode == "paper" and self._portfolio:
            notional = price * qty
            result = self._portfolio.open_position(
                symbol=self.symbol,
                side="long",
                qty=qty,
                entry_price=price
            )
            return {
                "ok": True,
                "action": "enter_long",
                "symbol": self.symbol,
                "price": price,
                "qty": qty,
                "notional_usd": notional,
                "reason": reason,
                "mode": self.mode,
                "timestamp": time.time()
            }
        else:
            # Real mode - TODO: implement real exchange execution
            return {
                "ok": False,
                "error": "Real mode not implemented yet",
                "mode": self.mode
            }
    
    def exit_position(self, price: float, reason: str = "signal") -> dict:
        """
        Exit current position.
        
        Args:
            price: Exit price
            reason: Exit reason (tp, sl, signal, etc.)
        
        Returns:
            Trade result dict
        """
        if self.mode == "paper" and self._portfolio:
            if self.symbol not in self._portfolio.positions:
                return {
                    "ok": False,
                    "error": "No open position",
                    "symbol": self.symbol
                }
            
            pos = self._portfolio.positions[self.symbol]
            result = self._portfolio.close_position(
                symbol=self.symbol,
                exit_price=price
            )
            
            return {
                "ok": True,
                "action": "exit_position",
                "symbol": self.symbol,
                "entry_price": pos.entry_price,
                "exit_price": price,
                "qty": pos.qty,
                "pnl_usd": result.get("pnl_usd", 0.0),
                "pnl_pct": result.get("pnl_pct", 0.0),
                "reason": reason,
                "mode": self.mode,
                "timestamp": time.time()
            }
        else:
            # Real mode - TODO
            return {
                "ok": False,
                "error": "Real mode not implemented yet",
                "mode": self.mode
            }
    
    def check_stop_loss(self, current_price: float, sl_pct: float) -> dict | None:
        """
        Check if stop loss is hit.
        
        Args:
            current_price: Current market price
            sl_pct: Stop loss percentage (e.g., 0.02 for 2%)
        
        Returns:
            Exit result if SL hit, None otherwise
        """
        if not self.has_position():
            return None
        
        if self.mode == "paper" and self._portfolio:
            pos = self._portfolio.positions[self.symbol]
            pos.update_pnl(current_price)
            
            # Check if loss exceeds stop loss threshold
            if pos.pnl_pct < -sl_pct * 100:
                return self.exit_position(current_price, reason="stop_loss")
        
        return None
    
    def check_take_profit(self, current_price: float, tp_pct: float) -> dict | None:
        """
        Check if take profit is hit.
        
        Args:
            current_price: Current market price
            tp_pct: Take profit percentage (e.g., 0.03 for 3%)
        
        Returns:
            Exit result if TP hit, None otherwise
        """
        if not self.has_position():
            return None
        
        if self.mode == "paper" and self._portfolio:
            pos = self._portfolio.positions[self.symbol]
            pos.update_pnl(current_price)
            
            # Check if profit exceeds take profit threshold
            if pos.pnl_pct >= tp_pct * 100:
                return self.exit_position(current_price, reason="take_profit")
        
        return None
    
    def get_position_pnl(self, current_price: float) -> dict:
        """Get current position PnL."""
        if not self.has_position():
            return {
                "has_position": False,
                "pnl_usd": 0.0,
                "pnl_pct": 0.0
            }
        
        if self.mode == "paper" and self._portfolio:
            pos = self._portfolio.positions[self.symbol]
            pos.update_pnl(current_price)
            
            return {
                "has_position": True,
                "entry_price": pos.entry_price,
                "current_price": current_price,
                "qty": pos.qty,
                "pnl_usd": pos.pnl_usd,
                "pnl_pct": pos.pnl_pct,
                "side": pos.side
            }
        
        return {
            "has_position": False,
            "pnl_usd": 0.0,
            "pnl_pct": 0.0
        }
    
    def get_portfolio_stats(self) -> dict:
        """Get overall portfolio statistics."""
        if self.mode == "paper" and self._portfolio:
            # Calculate total position value
            total_position_value = sum(
                pos.current_price * pos.qty
                for pos in self._portfolio.positions.values()
            )
            
            # Calculate equity
            equity = self._portfolio.cash_balance + total_position_value
            
            # Calculate total PnL
            total_pnl = sum(pos.pnl_usd for pos in self._portfolio.positions.values())
            total_pnl += sum(t.pnl_usd for t in self._portfolio.trades)
            
            # Calculate PnL percentage
            total_pnl_pct = (total_pnl / self._portfolio.starting_balance) * 100 if self._portfolio.starting_balance > 0 else 0
            
            # Calculate win rate
            winning_trades = sum(1 for t in self._portfolio.trades if t.pnl_usd > 0)
            total_trades = len(self._portfolio.trades)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            return {
                "cash_balance": self._portfolio.cash_balance,
                "total_position_value": total_position_value,
                "equity": equity,
                "total_pnl": total_pnl,
                "total_pnl_pct": total_pnl_pct,
                "num_trades": total_trades,
                "num_positions": len(self._portfolio.positions),
                "win_rate": win_rate
            }
        
        return {
            "cash_balance": 0.0,
            "equity": 0.0,
            "total_pnl": 0.0,
            "num_trades": 0,
            "num_positions": 0
        }


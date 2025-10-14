"""
Realtime Paper Trading Engine

Tick-driven PnL calculation with fair fill simulation.
NEVER fetches prices via REST - only uses streaming ticks.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from ..infra.db import write_equity_snapshot
from ..infra.logger import log_event
from ..infra.metrics import levibot_equity, levibot_realized_pnl_total, levibot_unrealized_pnl
from ..infra.redis_stream import get_last_tick
from .risk_guard import risk_guard
from .slippage import calculate_fee, slippage_price


class Position:
    """Open position."""
    def __init__(self, symbol: str, qty: float, avg_price: float, side: str = "long"):
        self.symbol = symbol
        self.qty = qty  # Positive for long, negative for short (conceptual)
        self.avg_price = avg_price
        self.side = side
        self.entry_time = time.time()
    
    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL."""
        if self.side == "long":
            return (current_price - self.avg_price) * self.qty
        else:
            return (self.avg_price - current_price) * abs(self.qty)


class RealtimePaperEngine:
    """
    Realtime paper trading engine.
    
    Features:
    - Tick-driven PnL updates (no REST calls)
    - Fair fill simulation with slippage
    - Risk guard integration
    - Metrics publishing
    - TimescaleDB equity curve
    """
    
    def __init__(self, starting_balance: float = 10000.0):
        self.balance = starting_balance
        self.starting_balance = starting_balance
        self.positions: dict[str, Position] = {}  # symbol -> Position
        self.unrealized_pnl = 0.0
        self.high_water_mark = starting_balance
        self.last_tick_prices: dict[str, float] = {}  # symbol -> last_price
        self.lock = asyncio.Lock()
    
    async def on_tick(self, tick: dict[str, Any]) -> None:
        """
        Process market tick update.
        
        Updates:
        - Last known price
        - Unrealized PnL for open positions
        - Equity curve metrics
        """
        symbol = tick.get("symbol")
        last_price = tick.get("last")
        
        if not symbol or not last_price:
            return
        
        async with self.lock:
            self.last_tick_prices[symbol] = float(last_price)
            
            # Recalculate unrealized PnL
            total_unrealized = 0.0
            for sym, pos in self.positions.items():
                if sym in self.last_tick_prices:
                    total_unrealized += pos.unrealized_pnl(self.last_tick_prices[sym])
            
            self.unrealized_pnl = total_unrealized
            
            # Update metrics
            equity = self.balance + self.unrealized_pnl
            levibot_equity.set(equity)
            levibot_unrealized_pnl.set(self.unrealized_pnl)
            
            # Track high water mark and drawdown
            self.high_water_mark = max(self.high_water_mark, equity)
            drawdown = equity - self.high_water_mark
            
            # Periodically snapshot equity curve (every 10 seconds)
            if int(time.time()) % 10 == 0:
                await write_equity_snapshot(
                    ts=time.time(),
                    balance=self.balance,
                    realized=self.balance - self.starting_balance,
                    unrealized=self.unrealized_pnl,
                    drawdown=drawdown,
                )
    
    async def execute_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        """
        Execute trading signal.
        
        Args:
            signal: Signal dict with keys: symbol, side, size, confidence, etc.
        
        Returns:
            Execution result
        """
        symbol = signal.get("symbol")
        side = signal.get("side", "").lower()
        size = signal.get("size", 0.0)
        
        if not symbol or side not in ["buy", "sell"] or size <= 0:
            return {"ok": False, "reason": "Invalid signal"}
        
        # Get current market price from Redis (NEVER REST)
        tick = await get_last_tick(symbol)
        if not tick or "last" not in tick:
            return {"ok": False, "reason": f"No market data for {symbol}"}
        
        mark_price = float(tick["last"])
        notional = mark_price * size
        
        # Risk check
        allowed, reason = risk_guard.allow(notional)
        if not allowed:
            log_event("ORDER_BLOCKED", {"symbol": symbol, "side": side, "reason": reason})
            return {"ok": False, "reason": reason}
        
        # Calculate fill price with slippage
        fill_price = slippage_price(mark_price, side, size)
        fee = calculate_fee(fill_price * size)
        
        async with self.lock:
            # Execute trade
            if side == "buy":
                # Open or add to long position
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    new_qty = pos.qty + size
                    new_avg = (pos.avg_price * pos.qty + fill_price * size) / new_qty
                    pos.qty = new_qty
                    pos.avg_price = new_avg
                else:
                    self.positions[symbol] = Position(symbol, size, fill_price, "long")
                
                # Deduct cost from balance
                self.balance -= (fill_price * size + fee)
            
            else:  # sell
                # Close or reduce position
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    qty_to_close = min(size, pos.qty)
                    
                    # Realize PnL
                    realized_pnl = (fill_price - pos.avg_price) * qty_to_close - fee
                    self.balance += (fill_price * qty_to_close - fee)
                    
                    # Update position
                    pos.qty -= qty_to_close
                    if pos.qty <= 0:
                        del self.positions[symbol]
                    
                    # Track realized PnL
                    risk_guard.update_daily_pnl(realized_pnl)
                    levibot_realized_pnl_total.inc(realized_pnl)
                    
                    log_event("TRADE_CLOSED", {
                        "symbol": symbol,
                        "qty": qty_to_close,
                        "price": fill_price,
                        "fee": fee,
                        "realized_pnl": realized_pnl,
                    })
                else:
                    # No position to close
                    return {"ok": False, "reason": "No position to close"}
        
        log_event("ORDER_FILLED", {
            "symbol": symbol,
            "side": side,
            "qty": size,
            "price": fill_price,
            "fee": fee,
            "source": signal.get("source", "unknown"),
        })
        
        return {
            "ok": True,
            "symbol": symbol,
            "side": side,
            "qty": size,
            "fill_price": fill_price,
            "fee": fee,
        }
    
    def get_portfolio_stats(self) -> dict[str, Any]:
        """Get current portfolio statistics."""
        equity = self.balance + self.unrealized_pnl
        return {
            "balance": self.balance,
            "unrealized_pnl": self.unrealized_pnl,
            "equity": equity,
            "positions_count": len(self.positions),
            "positions": [
                {
                    "symbol": pos.symbol,
                    "qty": pos.qty,
                    "avg_price": pos.avg_price,
                    "current_price": self.last_tick_prices.get(pos.symbol, 0),
                    "unrealized_pnl": pos.unrealized_pnl(self.last_tick_prices.get(pos.symbol, pos.avg_price)),
                }
                for pos in self.positions.values()
            ],
        }








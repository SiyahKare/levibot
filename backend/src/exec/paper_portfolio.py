"""
Paper Trading Portfolio Manager

Tracks paper trading balance, positions, PnL, and trade history.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass
class PaperPosition:
    """Open paper trading position."""

    symbol: str
    side: str  # "long" | "short"
    qty: float
    entry_price: float
    current_price: float
    entry_time: str
    pnl_usd: float = 0.0
    pnl_pct: float = 0.0

    def update_pnl(self, current_price: float):
        """Update PnL based on current market price."""
        self.current_price = current_price
        if self.side == "long":
            self.pnl_usd = (current_price - self.entry_price) * self.qty
        else:  # short
            self.pnl_usd = (self.entry_price - current_price) * self.qty

        if self.entry_price > 0:
            self.pnl_pct = (self.pnl_usd / (self.entry_price * self.qty)) * 100


@dataclass
class PaperTrade:
    """Closed paper trade record."""

    trade_id: str
    symbol: str
    side: str
    qty: float
    entry_price: float
    exit_price: float
    entry_time: str
    exit_time: str
    pnl_usd: float
    pnl_pct: float
    duration_sec: float


class PaperPortfolio:
    """
    Paper trading portfolio manager with persistence.

    Tracks:
    - Starting balance
    - Current cash balance
    - Open positions
    - Closed trades
    - Total PnL
    - Win rate
    """

    def __init__(self, starting_balance: float = 10000.0):
        self.starting_balance = starting_balance
        self.cash_balance = starting_balance
        self.positions: dict[str, PaperPosition] = {}
        self.trades: list[PaperTrade] = []
        self.lock = threading.Lock()
        self._loaded = False

        default_dirs = [
            os.getenv("DATA_DIR"),
            Path(__file__).resolve().parents[3] / "backend" / "data",
            Path.cwd() / "backend" / "data",
            Path(tempfile.gettempdir()) / "levibot" / "data",
        ]
        data_dir = None
        for cand in default_dirs:
            if not cand:
                continue
            cand_path = Path(cand)
            try:
                cand_path.mkdir(parents=True, exist_ok=True)
                data_dir = cand_path
                break
            except OSError:
                continue
        if data_dir is None:
            fallback = Path(__file__).resolve().parents[3] / "backend" / "data"
            fallback.mkdir(parents=True, exist_ok=True)
            data_dir = fallback

        self.data_file = data_dir / "paper_portfolio.json"
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

    def _ensure_loaded(self):
        """Lazy load portfolio data on first access."""
        if self._loaded:
            return

        if not self.data_file.exists():
            # Create initial empty state
            self.save()
            self._loaded = True
            return

        try:
            with open(self.data_file) as f:
                data = json.load(f)

            self.starting_balance = data.get("starting_balance", self.starting_balance)
            self.cash_balance = data.get("cash_balance", self.cash_balance)

            # Restore positions
            self.positions = {}
            for pos_data in data.get("positions", []):
                pos = PaperPosition(**pos_data)
                self.positions[pos.symbol] = pos

            # Restore trades
            self.trades = []
            for trade_data in data.get("trades", []):
                self.trades.append(PaperTrade(**trade_data))

            self._loaded = True

        except Exception as e:
            print(f"⚠️  Failed to load paper portfolio: {e}")
            self._loaded = True  # Mark as loaded anyway to avoid retry loop

    def save(self):
        """Save portfolio state to disk (fast, non-blocking)."""
        try:
            # Manual serialization to avoid asdict() overhead
            positions_data = [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "qty": p.qty,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "entry_time": p.entry_time,
                    "pnl_usd": p.pnl_usd,
                    "pnl_pct": p.pnl_pct,
                }
                for p in self.positions.values()
            ]

            trades_data = [
                {
                    "trade_id": t.trade_id,
                    "symbol": t.symbol,
                    "side": t.side,
                    "qty": t.qty,
                    "entry_price": t.entry_price,
                    "exit_price": t.exit_price,
                    "entry_time": t.entry_time,
                    "exit_time": t.exit_time,
                    "pnl_usd": t.pnl_usd,
                    "pnl_pct": t.pnl_pct,
                    "duration_sec": t.duration_sec,
                }
                for t in self.trades
            ]

            data = {
                "starting_balance": self.starting_balance,
                "cash_balance": self.cash_balance,
                "positions": positions_data,
                "trades": trades_data,
                "last_updated": datetime.now(UTC).isoformat(),
            }

            with open(self.data_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Failed to save paper portfolio: {e}")

    def open_position(
        self,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        notional: float,
    ) -> bool:
        """Open a new paper position."""
        with self.lock:
            # Check if we have enough cash
            if notional > self.cash_balance:
                return False

            # Close existing position if any
            if symbol in self.positions:
                self.close_position(symbol, price)

            # Deduct cash
            self.cash_balance -= notional

            # Create position
            self.positions[symbol] = PaperPosition(
                symbol=symbol,
                side=side,
                qty=qty,
                entry_price=price,
                current_price=price,
                entry_time=datetime.now(UTC).isoformat(),
            )

            self.save()
            return True

    def close_position(self, symbol: str, exit_price: float) -> PaperTrade | None:
        """Close an existing position and record the trade."""
        with self.lock:
            if symbol not in self.positions:
                return None

            pos = self.positions[symbol]

            # Calculate final PnL
            pos.update_pnl(exit_price)

            # Return cash
            exit_notional = exit_price * pos.qty
            self.cash_balance += exit_notional

            # Calculate duration
            entry_dt = datetime.fromisoformat(pos.entry_time.replace("Z", "+00:00"))
            exit_dt = datetime.now(UTC)
            duration = (exit_dt - entry_dt).total_seconds()

            # Record trade
            trade = PaperTrade(
                trade_id=f"{symbol}_{int(time.time())}",
                symbol=symbol,
                side=pos.side,
                qty=pos.qty,
                entry_price=pos.entry_price,
                exit_price=exit_price,
                entry_time=pos.entry_time,
                exit_time=exit_dt.isoformat(),
                pnl_usd=pos.pnl_usd,
                pnl_pct=pos.pnl_pct,
                duration_sec=duration,
            )
            self.trades.append(trade)

            # Remove position
            del self.positions[symbol]

            self.save()
            return trade

    def update_position_price(self, symbol: str, current_price: float) -> bool:
        """Update position with current market price for real-time PnL."""
        with self.lock:
            if symbol not in self.positions:
                return False

            pos = self.positions[symbol]
            pos.update_pnl(current_price)
            return True

    def update_prices(self, prices: dict[str, float]):
        """Update current prices for all open positions."""
        with self.lock:
            for symbol, price in prices.items():
                if symbol in self.positions:
                    self.positions[symbol].update_pnl(price)
            self.save()

    def get_total_equity(self) -> float:
        """Calculate total equity (cash + unrealized PnL)."""
        with self.lock:
            unrealized_pnl = sum(p.pnl_usd for p in self.positions.values())
            return self.cash_balance + unrealized_pnl

    def get_total_pnl(self) -> float:
        """Calculate total PnL (realized + unrealized)."""
        with self.lock:
            realized = sum(t.pnl_usd for t in self.trades)
            unrealized = sum(p.pnl_usd for p in self.positions.values())
            return realized + unrealized

    def get_stats(self) -> dict[str, Any]:
        """Get portfolio statistics."""
        self._ensure_loaded()
        with self.lock:
            winning_trades = [t for t in self.trades if t.pnl_usd > 0]
            losing_trades = [t for t in self.trades if t.pnl_usd < 0]

            total_trades = len(self.trades)
            win_count = len(winning_trades)
            loss_count = len(losing_trades)

            win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

            avg_win = (
                (sum(t.pnl_usd for t in winning_trades) / win_count)
                if win_count > 0
                else 0
            )
            avg_loss = (
                (sum(t.pnl_usd for t in losing_trades) / loss_count)
                if loss_count > 0
                else 0
            )

            # Calculate inline to avoid nested locks
            realized = sum(t.pnl_usd for t in self.trades)
            unrealized = sum(p.pnl_usd for p in self.positions.values())
            total_pnl = realized + unrealized
            total_equity = self.cash_balance + unrealized

            return {
                "starting_balance": self.starting_balance,
                "cash_balance": self.cash_balance,
                "total_equity": total_equity,
                "total_pnl": total_pnl,
                "total_pnl_pct": (
                    (total_pnl / self.starting_balance * 100)
                    if self.starting_balance > 0
                    else 0
                ),
                "open_positions": len(self.positions),
                "total_trades": total_trades,
                "winning_trades": win_count,
                "losing_trades": loss_count,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "profit_factor": abs(avg_win / avg_loss) if avg_loss != 0 else 0,
            }

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all open positions."""
        try:
            self._ensure_loaded()
            with self.lock:
                result = []
                for p in self.positions.values():
                    result.append(
                        {
                            "symbol": p.symbol,
                            "side": p.side,
                            "qty": p.qty,
                            "entry_price": p.entry_price,
                            "current_price": p.current_price,
                            "entry_time": p.entry_time,
                            "pnl_usd": p.pnl_usd,
                            "pnl_pct": p.pnl_pct,
                            "unrealized_pnl": p.pnl_usd,
                            "unrealized_pnl_pct": p.pnl_pct,
                            "opened_at": p.entry_time,
                            "notional": p.entry_price * p.qty,
                        }
                    )
                return result
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []

    def get_recent_trades(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent closed trades."""
        try:
            self._ensure_loaded()
            with self.lock:
                result = []
                for t in self.trades[-limit:][::-1]:  # Most recent first
                    result.append(
                        {
                            "id": t.trade_id,
                            "symbol": t.symbol,
                            "side": t.side,
                            "qty": t.qty,
                            "entry_price": t.entry_price,
                            "exit_price": t.exit_price,
                            "pnl_usd": t.pnl_usd,
                            "pnl_pct": t.pnl_pct,
                            "duration_sec": t.duration_sec,
                            "opened_at": t.entry_time,
                            "closed_at": t.exit_time,
                        }
                    )
                return result
        except Exception as e:
            print(f"Error getting trades: {e}")
            return []

    def reset(self, starting_balance: float | None = None):
        """Reset portfolio to starting state."""
        with self.lock:
            if starting_balance is not None:
                self.starting_balance = starting_balance

            self.cash_balance = self.starting_balance
            self.positions.clear()
            self.trades.clear()
            self.save()


# Global instance
_PORTFOLIO: PaperPortfolio | None = None


def get_paper_portfolio() -> PaperPortfolio:
    """Get or create global paper portfolio instance."""
    global _PORTFOLIO
    if _PORTFOLIO is None:
        starting_balance = float(os.getenv("PAPER_STARTING_BALANCE", "10000"))
        _PORTFOLIO = PaperPortfolio(starting_balance)
    return _PORTFOLIO

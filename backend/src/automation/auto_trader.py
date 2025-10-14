"""
Automatic Trading Bot - Demo Automation

Periodically executes trades based on simple rules.
Perfect for testing and demonstration of automated trading.
"""

import random
from datetime import datetime

from ..exec.paper_portfolio import get_paper_portfolio
from ..infra.logger import log_event
from ..infra.price_cache import get_price


class AutoTrader:
    """Automatic trading bot with configurable strategies."""

    def __init__(self):
        # Use internal functions instead of HTTP calls to avoid localhost issues in Docker
        self.enabled = False
        self.symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
        self.min_notional = 25
        self.max_notional = 100

    def execute_random_trade(self):
        """Execute a random buy trade for demonstration."""
        if not self.enabled:
            return

        try:
            portfolio = get_paper_portfolio()

            # Pick random symbol
            symbol = random.choice(self.symbols)

            # Random notional between min and max
            notional = random.randint(self.min_notional, self.max_notional)

            # Get current price
            price = get_price(symbol)
            if price is None:
                print(f"⚠️  Could not get price for {symbol}")
                return

            # Calculate quantity
            qty = notional / price

            # Execute trade
            success = portfolio.open_position(symbol, "long", qty, price, notional)

            if success:
                log_event(
                    "AUTO_TRADER_EXECUTED",
                    {
                        "symbol": symbol,
                        "side": "buy",
                        "notional": notional,
                        "price": price,
                        "qty": qty,
                    },
                    symbol=symbol,
                )
                print(f"🤖 Auto-Trade: BUY {symbol} ${notional} @ ${price:.2f}")
            else:
                print("❌ Auto-Trade failed: Insufficient balance")

        except Exception as e:
            print(f"⚠️  Auto-Trade error: {e}")

    def close_random_position(self):
        """Close a random open position if any exist."""
        if not self.enabled:
            return

        try:
            portfolio = get_paper_portfolio()

            # Get open positions
            positions = portfolio.get_positions()
            if not positions:
                print("ℹ️  No positions to close")
                return

            # Pick random position
            position = random.choice(positions)
            symbol = position.symbol

            # Get current price
            price = get_price(symbol)
            if price is None:
                print(f"⚠️  Could not get price for {symbol}")
                return

            # Close it
            trade = portfolio.close_position(symbol, price)

            if trade:
                log_event(
                    "AUTO_TRADER_CLOSED",
                    {
                        "symbol": symbol,
                        "pnl_usd": trade.pnl_usd,
                        "pnl_pct": trade.pnl_pct,
                        "entry_price": trade.entry_price,
                        "exit_price": trade.exit_price,
                    },
                    symbol=symbol,
                )
                pnl_sign = "+" if trade.pnl_usd >= 0 else ""
                print(
                    f"🤖 Auto-Close: {symbol} PnL: {pnl_sign}${trade.pnl_usd:.2f} ({trade.pnl_pct:.2f}%)"
                )
            else:
                print("❌ Auto-Close failed: No position found")

        except Exception as e:
            print(f"⚠️  Auto-Close error: {e}")

    def run_cycle(self):
        """Run one automation cycle - either open or close position."""
        if not self.enabled:
            return

        try:
            portfolio = get_paper_portfolio()

            # Get current positions
            open_positions = len(portfolio.get_positions())

            print(
                f"\n⚡ Auto-Trader Cycle [{datetime.now().strftime('%H:%M:%S')}] - Open: {open_positions}"
            )

            # Decision logic: 70% chance to buy if < 3 positions, else close
            if open_positions < 3 and random.random() < 0.7:
                self.execute_random_trade()
            elif open_positions > 0:
                self.close_random_position()
            else:
                print("ℹ️  Waiting for next cycle...")

        except Exception as e:
            print(f"⚠️  Auto-Trader cycle error: {e}")


# Global instance
_AUTO_TRADER = None


def get_auto_trader() -> AutoTrader:
    """Get or create global auto-trader instance."""
    global _AUTO_TRADER
    if _AUTO_TRADER is None:
        _AUTO_TRADER = AutoTrader()
    return _AUTO_TRADER

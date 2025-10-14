"""
Auto-Trade API - Simplified Signal to Execution Pipeline

Directly processes trading signals and executes them on paper portfolio
with real prices, risk management, and full logging.
"""

from typing import Any

from fastapi import APIRouter, Body

from ...exec.paper_portfolio import get_paper_portfolio
from ...infra.logger import log_event
from ...infra.price_cache import get_price

router = APIRouter(prefix="/trade", tags=["autotrade"])


@router.post("/auto")
async def auto_trade(
    symbol: str = Body(..., description="Trading symbol (e.g., BTCUSDT)"),
    side: str = Body(..., description="buy | sell"),
    notional_usd: float = Body(50.0, description="Trade size in USD"),
    source: str = Body("api", description="Signal source"),
) -> dict[str, Any]:
    """
    Execute auto-trade with real prices and risk management.

    Pipeline:
    1. Validate inputs
    2. Get real price from CoinGecko
    3. Calculate quantity
    4. Risk checks (balance, limits)
    5. Execute on paper portfolio
    6. Log events
    7. Return result
    """

    # Normalize symbol
    symbol_clean = symbol.replace("/", "").upper()
    side_norm = side.lower()

    if side_norm not in ["buy", "sell"]:
        return {"ok": False, "error": "side must be 'buy' or 'sell'"}

    # Log signal received
    log_event(
        "AUTO_TRADE_SIGNAL",
        {
            "symbol": symbol_clean,
            "side": side_norm,
            "notional_usd": notional_usd,
            "source": source,
        },
        symbol=symbol_clean,
    )

    # Get real price from CoinGecko
    price = get_price(symbol)
    if price is None:
        return {
            "ok": False,
            "error": f"Could not fetch price for {symbol}",
            "symbol": symbol_clean,
        }

    # Calculate quantity
    qty = notional_usd / price

    portfolio = get_paper_portfolio()

    if side_norm == "buy":
        # Open long position
        success = portfolio.open_position(
            symbol_clean, "long", qty, price, notional_usd
        )

        if not success:
            log_event(
                "AUTO_TRADE_FAILED",
                {
                    "reason": "insufficient_balance",
                    "symbol": symbol_clean,
                    "side": side_norm,
                    "notional": notional_usd,
                },
                symbol=symbol_clean,
            )
            return {
                "ok": False,
                "error": "Insufficient balance",
                "symbol": symbol_clean,
                "required": notional_usd,
                "available": portfolio.cash_balance,
            }

        # Log success
        log_event(
            "AUTO_TRADE_EXECUTED",
            {
                "action": "open_position",
                "symbol": symbol_clean,
                "side": "long",
                "qty": qty,
                "price": price,
                "notional": notional_usd,
            },
            symbol=symbol_clean,
        )

        log_event(
            "POSITION_OPENED",
            {
                "symbol": symbol_clean,
                "side": "long",
                "qty": qty,
                "price": price,
                "notional": notional_usd,
            },
            symbol=symbol_clean,
        )

        return {
            "ok": True,
            "action": "opened",
            "symbol": symbol_clean,
            "side": "long",
            "qty": qty,
            "price": price,
            "notional": notional_usd,
            "source": "coingecko",
            "portfolio": {
                "cash_balance": portfolio.cash_balance,
                "open_positions": len(portfolio.positions),
            },
        }

    else:  # sell
        # Close existing position
        trade = portfolio.close_position(symbol_clean, price)

        if not trade:
            log_event(
                "AUTO_TRADE_FAILED",
                {
                    "reason": "no_position_to_close",
                    "symbol": symbol_clean,
                    "side": side_norm,
                },
                symbol=symbol_clean,
            )
            return {
                "ok": False,
                "error": f"No open position for {symbol_clean}",
                "symbol": symbol_clean,
            }

        # Log success with PnL
        log_event(
            "AUTO_TRADE_EXECUTED",
            {
                "action": "close_position",
                "symbol": symbol_clean,
                "pnl_usd": trade.pnl_usd,
                "pnl_pct": trade.pnl_pct,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "duration_sec": trade.duration_sec,
            },
            symbol=symbol_clean,
        )

        log_event(
            "POSITION_CLOSED",
            {
                "symbol": symbol_clean,
                "pnl_usdt": trade.pnl_usd,
                "pnl_pct": trade.pnl_pct,
                "qty": trade.qty,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "duration_sec": trade.duration_sec,
            },
            symbol=symbol_clean,
        )

        stats = portfolio.get_stats()

        return {
            "ok": True,
            "action": "closed",
            "symbol": symbol_clean,
            "pnl_usd": trade.pnl_usd,
            "pnl_pct": trade.pnl_pct,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "duration_sec": trade.duration_sec,
            "source": "coingecko",
            "portfolio": {
                "total_equity": stats["total_equity"],
                "total_pnl": stats["total_pnl"],
                "win_rate": stats["win_rate"],
                "total_trades": stats["total_trades"],
            },
        }


@router.get("/status")
async def get_trading_status() -> dict[str, Any]:
    """Get current trading system status."""
    portfolio = get_paper_portfolio()
    stats = portfolio.get_stats()
    positions = portfolio.get_positions()

    return {
        "ok": True,
        "status": "active",
        "portfolio": {
            "starting_balance": stats["starting_balance"],
            "cash_balance": stats["cash_balance"],
            "total_equity": stats["total_equity"],
            "total_pnl": stats["total_pnl"],
            "total_pnl_pct": stats["total_pnl_pct"],
        },
        "stats": {
            "total_trades": stats["total_trades"],
            "winning_trades": stats["winning_trades"],
            "losing_trades": stats["losing_trades"],
            "win_rate": stats["win_rate"],
            "profit_factor": stats["profit_factor"],
        },
        "positions": {
            "open": len(positions),
            "details": positions,
        },
    }

"""
Paper Trading Portfolio API

Provides endpoints for paper trading portfolio management and monitoring.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Body
from pydantic import BaseModel

from ...exec import get_executor
from ...exec.paper_portfolio import get_paper_portfolio
from ...infra.db_trades import insert_trade
from ...infra.logger import log_event

router = APIRouter(prefix="/paper", tags=["paper"])


class TradeRequest(BaseModel):
    """Test trade request model"""

    symbol: str
    side: Literal["buy", "sell"]
    notional_usd: float


# Thread pool for MEXC price fetching
_executor_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mexc_price")


def _fetch_price_sync(symbol: str) -> float | None:
    """Synchronous MEXC price fetch (runs in thread pool)."""
    try:
        executor = get_executor()
        if executor and hasattr(executor, "fetch_ticker_price"):
            return executor.fetch_ticker_price(symbol)
    except Exception as e:
        print(f"⚠️ MEXC fetch failed for {symbol}: {e}")
    return None


def get_mexc_price_sync(symbol: str) -> float | None:
    """
    Fetch real-time price from MEXC.

    **CURRENTLY DISABLED** - Always returns None (mock fallback)

    TODO: Re-enable when MEXC stability issues are resolved
    """
    # DISABLED - Too many blocking issues
    return None

    # try:
    #     # Run sync fetch in thread pool with timeout
    #     loop = asyncio.get_event_loop()
    #     future = loop.run_in_executor(_executor_pool, _fetch_price_sync, symbol)
    #     price = await asyncio.wait_for(future, timeout=timeout_sec)
    #     return price
    # except TimeoutError:
    #     print(f"⚠️ MEXC price timeout for {symbol} ({timeout_sec}s)")
    #     return None
    # except Exception as e:
    #     print(f"⚠️ MEXC price error for {symbol}: {e}")
    #     return None


async def _ai_reason_safe(
    symbol: str,
    side: str,
    qty: float,
    price: float,
    confidence: float,
    context: str = "",
) -> str:
    """
    Generate AI trade reason with market context and safety fallbacks.

    - Market context: last price, 1m return, spread
    - Budget tracking: monthly token limit
    - Timeout: configurable (default 1.2s)
    - Returns "-" on failure or disabled
    """
    try:
        from ...ai.openai_client import brief_reason_plus
        from ...infra.market_context import build_context

        # Get market context
        ctx = await build_context(symbol)

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        reason = await loop.run_in_executor(
            None,
            lambda: brief_reason_plus(
                symbol, side, qty, price, confidence, context[:240], ctx
            ),
        )
        return reason
    except TimeoutError:
        return f"{side.upper()} @ ${price:.2f} (timeout)"
    except Exception:
        return f"{side.upper()} @ ${price:.2f}"


async def _persist_buy_trade(
    symbol: str, qty: float, price: float, strategy: str, confidence: float
) -> None:
    """Persist BUY trade to database."""
    try:
        # Generate AI reason (with timeout)
        reason = await _ai_reason_safe(
            symbol, "buy", qty, price, confidence, "paper_buy"
        )

        # Calculate fee (0.1% taker fee)
        fee = qty * price * 0.001

        # Insert trade
        await insert_trade(
            {
                "ts": datetime.utcnow(),
                "symbol": symbol,
                "side": "buy",
                "qty": qty,
                "price": price,
                "fee": fee,
                "strategy": strategy,
                "reason": reason,
                "confidence": confidence,
            }
        )
    except Exception as e:
        print(f"⚠️  Failed to persist BUY trade: {e}")


async def _persist_sell_trade(
    symbol: str, qty: float, price: float, pnl: float, strategy: str, confidence: float
) -> None:
    """Persist SELL trade to database."""
    try:
        # Generate AI reason (with timeout)
        context = f"pnl={pnl:.2f}"
        reason = await _ai_reason_safe(symbol, "sell", qty, price, confidence, context)

        # Calculate fee (0.1% taker fee)
        fee = qty * price * 0.001

        # Insert trade
        await insert_trade(
            {
                "ts": datetime.utcnow(),
                "symbol": symbol,
                "side": "sell",
                "qty": qty,
                "price": price,
                "fee": fee,
                "strategy": strategy,
                "reason": reason,
                "confidence": confidence,
            }
        )
    except Exception as e:
        print(f"⚠️  Failed to persist SELL trade: {e}")


async def _log_signal(symbol: str, side: str, confidence: float, strategy: str) -> None:
    """Log signal to in-memory signal log."""
    try:
        import time

        from ..routes.ops import _SIGNAL_LOG

        signal = {
            "ts": time.time(),
            "symbol": symbol,
            "side": side,
            "confidence": confidence,
            "strategy": strategy,
            "source": "api",
        }

        _SIGNAL_LOG.insert(0, signal)
        del _SIGNAL_LOG[100:]

    except Exception as e:
        print(f"⚠️  Failed to log signal: {e}")


@router.get("/health")
async def paper_health() -> dict[str, Any]:
    """Quick health check for paper trading system."""
    return {"ok": True, "status": "operational"}


@router.get("/portfolio")
async def get_portfolio_stats() -> dict[str, Any]:
    """
    Get paper trading portfolio statistics.

    Returns:
        - starting_balance: Initial capital
        - cash_balance: Available cash
        - total_equity: Cash + unrealized PnL
        - total_pnl: Total profit/loss
        - open_positions: Number of open positions
        - total_trades: Total completed trades
        - win_rate: Win rate percentage
        - profit_factor: Avg win / avg loss ratio
    """
    try:
        portfolio = get_paper_portfolio()
        stats = portfolio.get_stats()
        return {"ok": True, **stats}
    except Exception as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__}


@router.get("/positions")
async def get_open_positions() -> dict[str, Any]:
    """
    Get all open paper trading positions with real-time prices.

    Returns list of positions with:
        - symbol: Trading pair
        - side: long | short
        - qty: Position size
        - entry_price: Entry price
        - current_price: Current market price (real-time)
        - pnl_usd: Unrealized PnL in USD
        - pnl_pct: Unrealized PnL in %
        - entry_time: Position open timestamp
    """
    portfolio = get_paper_portfolio()

    # Mock prices as fallback
    mock_prices = {
        "BTCUSDT": 112000.0,
        "ETHUSDT": 3900.0,
        "SOLUSDT": 220.0,
        "BNBUSDT": 680.0,
    }

    # Update positions with mock prices (MEXC disabled)
    for symbol in list(portfolio.positions.keys()):
        # Use mock prices only (MEXC disabled)
        current_price = mock_prices.get(symbol, portfolio.positions[symbol].entry_price)
        portfolio.update_position_price(symbol, current_price)

    positions = portfolio.get_positions()
    return {"ok": True, "positions": positions, "count": len(positions)}


@router.get("/trades")
async def get_trade_history(limit: int = 50) -> dict[str, Any]:
    """
    Get recent closed trade history.

    Args:
        limit: Max number of trades to return (default: 50)

    Returns list of trades with:
        - trade_id: Unique trade ID
        - symbol: Trading pair
        - side: long | short
        - qty: Position size
        - entry_price: Entry price
        - exit_price: Exit price
        - pnl_usd: Realized PnL in USD
        - pnl_pct: Realized PnL in %
        - duration_sec: Trade duration in seconds
        - entry_time, exit_time: Timestamps
    """
    portfolio = get_paper_portfolio()
    trades = portfolio.get_recent_trades(limit)
    return {"ok": True, "trades": trades, "count": len(trades)}


@router.post("/test_trade")
def test_trade(req: TradeRequest) -> dict[str, Any]:
    """
    Execute a test paper trade (simplified for testing).

    Args:
        req: Trade request (symbol, side, notional_usd)

    Returns:
        Trade execution result
    """
    try:
        portfolio = get_paper_portfolio()

        # Mock prices as fallback
        mock_prices = {
            "BTCUSDT": 112000.0,
            "ETHUSDT": 3900.0,
            "SOLUSDT": 220.0,
            "BNBUSDT": 680.0,
        }

        # Use mock prices only (MEXC disabled)
        price = mock_prices.get(req.symbol, 100.0)

        qty = req.notional_usd / price

        if req.side == "buy":
            success = portfolio.open_position(
                symbol=req.symbol,
                side="long",
                qty=qty,
                price=price,
                notional=req.notional_usd,
            )
            if success:
                # Skip AI reason for now (too slow)
                # await _persist_buy_trade(req.symbol, qty, price, "test", 0.5)
                return {
                    "ok": True,
                    "action": "opened",
                    "symbol": req.symbol,
                    "qty": qty,
                    "price": price,
                    "notional": req.notional_usd,
                }
            return {"ok": False, "error": "Insufficient balance"}

        elif req.side == "sell":
            # Close any long position
            if req.symbol in portfolio.positions:
                pos = portfolio.positions[req.symbol]
                success = portfolio.close_position(req.symbol, price)
                if success:
                    return {
                        "ok": True,
                        "action": "closed",
                        "symbol": req.symbol,
                        "pnl": pos.unrealized_pnl,
                    }
            return {"ok": False, "error": "No position to close"}

        return {"ok": False, "error": "Invalid side"}

    except Exception as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__}


@router.post("/reset")
async def reset_portfolio(starting_balance: float = 10000.0) -> dict[str, Any]:
    """
    Reset paper trading portfolio to starting state.

    Args:
        starting_balance: New starting balance (default: 10000)

    WARNING: This will clear all positions and trade history!
    """
    portfolio = get_paper_portfolio()
    portfolio.reset(starting_balance)
    return {
        "ok": True,
        "message": "Portfolio reset successfully",
        "starting_balance": starting_balance,
    }


@router.post("/order")
async def place_order(
    symbol: str = Body(...),
    side: str = Body(...),
    notional_usd: float = Body(...),
    strategy: str = Body("manual"),
    confidence: float = Body(0.0),
) -> dict[str, Any]:
    """
    Place a paper trading order (high-level interface).

    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        side: buy | sell
        notional_usd: Order size in USD
        strategy: Strategy name (default: manual)
        confidence: Signal confidence (0.0-1.0, default: 0.0)

    Returns order result with position details or PnL.
    """
    portfolio = get_paper_portfolio()

    # Fetch current price (mock for now, replace with real market data in production)
    # For paper trading, we'll use a fixed mock price per symbol
    mock_prices = {
        "BTCUSDT": 50000.0,
        "ETHUSDT": 3000.0,
        "SOLUSDT": 100.0,
    }
    price = mock_prices.get(symbol, 100.0)
    qty = notional_usd / price

    if side.lower() == "buy":
        # Open long position
        success = portfolio.open_position(symbol, "long", qty, price, notional_usd)
        if not success:
            return {"ok": False, "error": "Insufficient balance"}

        # Log position opened
        log_event(
            "POSITION_OPENED",
            {
                "symbol": symbol,
                "side": "buy",
                "qty": qty,
                "price": price,
                "notional": notional_usd,
            },
            symbol=symbol,
        )

        # Log signal (if not manual)
        if strategy != "manual" and confidence > 0:
            asyncio.create_task(_log_signal(symbol, side, confidence, strategy))

        # Persist trade to DB (fire-and-forget)
        asyncio.create_task(
            _persist_buy_trade(
                symbol, qty, price, strategy=strategy, confidence=confidence
            )
        )

        return {
            "ok": True,
            "symbol": symbol,
            "side": "buy",
            "qty": qty,
            "price": price,
            "pnl_usd": 0.0,
        }

    else:  # sell
        # Close existing position
        trade = portfolio.close_position(symbol, price)
        if not trade:
            return {"ok": False, "error": "No position to close"}

        # Log position closed with PnL
        log_event(
            "POSITION_CLOSED",
            {
                "symbol": symbol,
                "side": "sell",
                "pnl_usdt": trade.pnl_usd,
                "pnl_pct": trade.pnl_pct,
                "qty": trade.qty,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "duration_sec": trade.duration_sec,
            },
            symbol=symbol,
        )

        # Persist trade to DB (fire-and-forget)
        asyncio.create_task(
            _persist_sell_trade(
                symbol,
                trade.qty,
                trade.exit_price,
                trade.pnl_usd,
                strategy=strategy,
                confidence=confidence,
            )
        )

        return {
            "ok": True,
            "symbol": symbol,
            "side": "sell",
            "qty": trade.qty,
            "price": trade.exit_price,
            "pnl_usd": trade.pnl_usd,
        }


@router.post("/trade")
async def execute_trade(
    symbol: str = Body(...),
    side: str = Body(...),
    qty: float = Body(...),
    price: float = Body(...),
) -> dict[str, Any]:
    """
    Execute a paper trade (open or close position).

    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        side: buy | sell
        qty: Quantity
        price: Execution price

    Returns trade result with PnL if closing a position.
    """
    portfolio = get_paper_portfolio()
    notional = qty * price

    if side.lower() == "buy":
        # Open long position
        success = portfolio.open_position(symbol, "long", qty, price, notional)
        if not success:
            return {"ok": False, "error": "Insufficient balance"}

        # Log position opened
        log_event(
            "POSITION_OPENED",
            {
                "symbol": symbol,
                "side": "long",
                "qty": qty,
                "price": price,
                "notional": notional,
            },
            symbol=symbol,
        )

        return {
            "ok": True,
            "action": "opened",
            "symbol": symbol,
            "side": "long",
            "qty": qty,
            "price": price,
            "notional": notional,
        }

    else:  # sell
        # Close existing position
        trade = portfolio.close_position(symbol, price)
        if not trade:
            return {"ok": False, "error": "No position to close"}

        # Log position closed with PnL
        log_event(
            "POSITION_CLOSED",
            {
                "symbol": symbol,
                "pnl_usdt": trade.pnl_usd,
                "pnl_pct": trade.pnl_pct,
                "qty": trade.qty,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "duration_sec": trade.duration_sec,
            },
            symbol=symbol,
        )

        return {
            "ok": True,
            "action": "closed",
            "symbol": symbol,
            "pnl_usd": trade.pnl_usd,
            "pnl_pct": trade.pnl_pct,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "duration_sec": trade.duration_sec,
        }


@router.get("/performance")
async def get_performance_chart() -> dict[str, Any]:
    """
    Get portfolio equity curve for charting.

    Returns:
        - equity_curve: List of {timestamp, equity} points
        - trades_timeline: List of trades with timestamps
    """
    portfolio = get_paper_portfolio()
    stats = portfolio.get_stats()
    trades = portfolio.get_recent_trades(100)

    # Build equity curve from trade history
    equity_curve = [{"timestamp": "start", "equity": stats["starting_balance"]}]

    running_equity = stats["starting_balance"]
    for trade in reversed(trades):  # Oldest first
        running_equity += trade["pnl_usd"]
        equity_curve.append(
            {
                "timestamp": trade["exit_time"],
                "equity": running_equity,
                "pnl": trade["pnl_usd"],
                "symbol": trade["symbol"],
            }
        )

    return {
        "ok": True,
        "equity_curve": equity_curve,
        "current_equity": stats["total_equity"],
        "total_return_pct": stats["total_pnl_pct"],
    }


@router.get("/summary")
async def get_summary() -> dict[str, Any]:
    """
    Get comprehensive paper trading summary.

    Combines portfolio stats, positions, and recent trades.
    """
    portfolio = get_paper_portfolio()

    return {
        "ok": True,
        "stats": portfolio.get_stats(),
        "positions": portfolio.get_positions(),
        "recent_trades": portfolio.get_recent_trades(10),
    }

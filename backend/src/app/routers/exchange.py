"""
Exchange health & balance endpoints.

Provides runtime diagnostics for configured exchange connections.
"""

from typing import Any

from fastapi import APIRouter, HTTPException

from ...exec import get_executor
from ...exec.paper_ccxt import place_cex_paper_order

router = APIRouter(prefix="/exchange", tags=["exchange"])


@router.get("/ping")
async def exchange_ping() -> dict[str, Any]:
    """
    Health check for exchange connectivity.

    Returns:
        - ok: bool
        - exchange: str (mexc | paper)
        - markets_count: int (if MEXC)
    """
    executor = get_executor()

    if executor is None:
        # Paper mode
        return {
            "ok": True,
            "exchange": "paper",
            "mode": "simulation",
            "note": "No live exchange configured",
        }

    # MEXC mode
    if hasattr(executor, "health_check"):
        result = executor.health_check()
        return result

    return {"ok": False, "error": "Executor does not support health checks"}


@router.get("/balance")
async def exchange_balance() -> dict[str, Any]:
    """
    Fetch account balance from configured exchange.

    Returns:
        - ok: bool
        - balance: dict (if MEXC)
        - error: str (if failed)
    """
    executor = get_executor()

    if executor is None:
        return {
            "ok": False,
            "error": "Paper mode - no real balance available",
            "note": "Use EXCHANGE=MEXC to connect to live exchange",
        }

    # MEXC mode
    if hasattr(executor, "get_balance"):
        result = executor.get_balance()
        return result

    return {"ok": False, "error": "Executor does not support balance queries"}


@router.get("/markets")
async def exchange_markets(limit: int = 20) -> dict[str, Any]:
    """
    List available trading markets.

    Args:
        limit: Max number of markets to return

    Returns:
        - ok: bool
        - markets: list of symbol names
        - total: int
    """
    executor = get_executor()

    if executor is None:
        return {
            "ok": False,
            "error": "Paper mode - markets not available",
        }

    # MEXC mode
    if hasattr(executor, "load_markets"):
        try:
            markets = executor.load_markets()
            symbols = list(markets.keys())
            return {
                "ok": True,
                "exchange": "mexc",
                "total": len(symbols),
                "markets": symbols[:limit],
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    return {"ok": False, "error": "Executor does not support market listing"}


@router.get("/ticker/{symbol}")
async def exchange_ticker(symbol: str) -> dict[str, Any]:
    """
    Fetch current ticker price for a symbol.

    Args:
        symbol: Trading pair (e.g., BTCUSDT or BTC/USDT)

    Returns:
        - ok: bool
        - symbol: str (normalized)
        - price: float
        - error: str (if failed)
    """
    executor = get_executor()

    if executor is None:
        return {
            "ok": False,
            "error": "Paper mode - use /dex/quote for synthetic prices",
        }

    # MEXC mode
    if hasattr(executor, "fetch_ticker_price"):
        try:
            norm_sym = executor.normalize_symbol(symbol)
            price = executor.fetch_ticker_price(symbol)
            return {
                "ok": True,
                "exchange": "mexc",
                "symbol": norm_sym,
                "price": price,
            }
        except Exception as e:
            return {"ok": False, "symbol": symbol, "error": str(e)}

    return {"ok": False, "error": "Executor does not support ticker queries"}


@router.post("/test-order")
async def test_order(
    symbol: str,
    side: str,
    notional_usd: float,
    dry_run: bool = True,
) -> dict[str, Any]:
    """
    Test order placement (dry-run by default for safety).

    Args:
        symbol: Trading pair
        side: "buy" or "sell"
        notional_usd: Order size in USD
        dry_run: If True, simulate order without execution (default: True)

    Returns:
        Execution result dict
    """
    if dry_run:
        # Paper mode simulation
        result = place_cex_paper_order(
            exchange="mexc",
            symbol=symbol,
            side=side,
            notional_usd=notional_usd,
        )
        return {
            "ok": result.ok,
            "mode": "dry_run",
            "symbol": result.symbol,
            "side": result.side,
            "qty": result.qty,
            "price": result.price,
            "filled": result.filled,
        }

    # LIVE ORDER (use with caution!)
    executor = get_executor()
    if executor is None:
        raise HTTPException(400, "Live orders require EXCHANGE=MEXC configuration")

    if not hasattr(executor, "place_market_order"):
        raise HTTPException(400, "Executor does not support order placement")

    result = executor.place_market_order(symbol, side, notional_usd)
    return {
        "ok": result.ok,
        "mode": "live",
        "symbol": result.symbol,
        "side": result.side,
        "qty": result.qty,
        "price": result.price,
        "filled": result.filled,
    }

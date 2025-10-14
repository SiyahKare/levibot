"""
Dev/Debug API Routes
Testing and debugging endpoints
"""

from typing import Literal

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ...exchange.mexc_filters import get_filters_cache, normalize_order

router = APIRouter(prefix="/dev", tags=["dev"])


class NormalizeRequest(BaseModel):
    """Request model for order normalization"""

    symbol: str
    side: Literal["BUY", "SELL"]
    quote_usd: float
    mid_price: float | None = None


@router.get("/filters")
async def get_symbol_filters(
    symbol: str = Query(
        ..., description="Symbol to get filters for (e.g., BTCUSDT, BTC/USDT, btc/usdt)"
    )
):
    """
    Get MEXC exchange filters for a symbol (with normalization)

    Supports multiple formats:
    - BTCUSDT
    - BTC/USDT
    - btc/usdt
    - BTC/USDT:USDT

    Returns:
        {
            "ok": true,
            "symbol_input": "BTCUSDT",
            "symbol_normalized": "BTC/USDT",
            "filters": {
                "price_step": 0.01,
                "qty_step": 0.00001,
                "min_notional": 5.0,
                "min_qty": 0.00001,
                "max_qty": 1000000.0,
                "price_precision": 2,
                "quantity_precision": 6
            }
        }
    """
    from ...exchange.mexc_filters import normalize_symbol

    cache = get_filters_cache()
    filters = await cache.get_filters(symbol)

    if not filters:
        return {
            "ok": False,
            "symbol_input": symbol,
            "error": "Filters not found for symbol. Try: BTCUSDT, BTC/USDT, or check if symbol exists on MEXC.",
        }

    # Get normalized symbol for display
    normalized = normalize_symbol(symbol, cache._symbol_map) or symbol

    return {
        "ok": True,
        "symbol_input": symbol,
        "symbol_normalized": normalized,
        "filters": {
            "price_step": filters.price_step,
            "qty_step": filters.qty_step,
            "min_notional": filters.min_notional,
            "min_qty": filters.min_qty,
            "max_qty": filters.max_qty,
            "price_precision": filters.price_precision,
            "quantity_precision": filters.quantity_precision,
        },
    }


@router.post("/normalize")
async def normalize_order_endpoint(req: NormalizeRequest):
    """
    Normalize an order to MEXC exchange filters (dry-run)

    Request:
        {
            "symbol": "BTC/USDT",
            "side": "BUY",
            "quote_usd": 150.0,
            "mid_price": 62850.0  // optional
        }

    Returns:
        {
            "ok": true,
            "order": {
                "symbol": "BTC/USDT",
                "side": "BUY",
                "price": 62850.0,
                "quantity": 0.00238,
                "notional": 149.583,
                "quote_usd": 150.0,
                "is_valid": true,
                "reject_reason": null
            }
        }
    """
    order = await normalize_order(
        symbol=req.symbol,
        side=req.side,
        quote_usd=req.quote_usd,
        mid_price=req.mid_price,
    )

    return {
        "ok": order.is_valid,
        "order": {
            "symbol": order.symbol,
            "side": order.side,
            "price": order.price,
            "quantity": order.quantity,
            "notional": order.notional,
            "quote_usd": order.quote_usd,
            "is_valid": order.is_valid,
            "reject_reason": order.reject_reason,
        },
    }


@router.get("/health")
def dev_health():
    """Dev endpoint health check"""
    return {"ok": True, "message": "Dev endpoints active"}

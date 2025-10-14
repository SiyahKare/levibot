"""
Price Cache API

Real-time cryptocurrency prices via CoinGecko with caching.
"""

from typing import Any

from fastapi import APIRouter, Query

from ...infra.price_cache import get_price, get_price_cache, get_prices_batch

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/quote/{symbol}")
async def get_symbol_price(symbol: str) -> dict[str, Any]:
    """
    Get current price for a symbol.

    Args:
        symbol: Trading symbol (e.g., "BTCUSDT", "BTC", "ETH")

    Returns:
        - ok: bool
        - symbol: str
        - price: float (USD)
        - cached: bool
        - source: "coingecko"
    """
    price = get_price(symbol)

    if price is None:
        return {
            "ok": False,
            "symbol": symbol,
            "error": "Price not available",
        }

    return {
        "ok": True,
        "symbol": symbol,
        "price": price,
        "currency": "USD",
        "source": "coingecko",
    }


@router.get("/batch")
async def get_batch_prices(
    symbols: str = Query(..., description="Comma-separated list of symbols")
) -> dict[str, Any]:
    """
    Get prices for multiple symbols.

    Args:
        symbols: Comma-separated symbols (e.g., "BTC,ETH,SOL")

    Returns:
        - ok: bool
        - prices: dict of symbol -> price
        - count: int
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]

    if not symbol_list:
        return {"ok": False, "error": "No symbols provided"}

    prices = get_prices_batch(symbol_list)

    return {
        "ok": True,
        "prices": prices,
        "count": len(prices),
        "source": "coingecko",
    }


@router.get("/cache/stats")
async def get_cache_stats() -> dict[str, Any]:
    """
    Get price cache statistics.

    Returns cache metrics like total cached, fresh vs stale entries.
    """
    cache = get_price_cache()
    stats = cache.get_cache_stats()

    return {
        "ok": True,
        **stats,
    }


@router.post("/cache/clear")
async def clear_price_cache() -> dict[str, Any]:
    """
    Clear all cached prices.

    Forces fresh fetch on next request.
    """
    cache = get_price_cache()
    cache.clear_cache()

    return {
        "ok": True,
        "message": "Price cache cleared",
    }


@router.get("/supported")
async def get_supported_symbols() -> dict[str, Any]:
    """
    Get list of supported symbols.

    Returns symbols that can be queried via CoinGecko.
    """
    from ...infra.price_cache import SYMBOL_MAP

    symbols = list(SYMBOL_MAP.keys())

    return {
        "ok": True,
        "symbols": sorted(symbols),
        "count": len(symbols),
        "note": "Add USDT/USD suffix for trading pairs (e.g., BTCUSDT)",
    }

"""
Market Context Builder
Provides market data context for AI reasoning
"""

from typing import Any


async def build_context(symbol: str) -> dict[str, Any]:
    """
    Build market context for a given symbol.

    Args:
        symbol: Trading pair (e.g., BTCUSDT)

    Returns:
        Dictionary containing:
        - last_px: Last traded price
        - ret_1m: 1-minute return (percentage change)
        - spread_bps: Bid-ask spread in basis points (if available)
    """
    try:
        from .db import get_pool

        pool = await get_pool()
        if not pool:
            return {"last_px": None, "ret_1m": None, "spread_bps": None}

        async with pool.acquire() as con:
            # Get last tick
            last = await con.fetchrow(
                "SELECT ts, last FROM market_ticks WHERE symbol = $1 ORDER BY ts DESC LIMIT 1",
                symbol,
            )

            # Get 1-minute window (first and last price)
            one_min = await con.fetchrow(
                """
                SELECT 
                    first(last, ts) AS first_px, 
                    last(last, ts) AS last_px
                FROM market_ticks
                WHERE symbol = $1 AND ts >= now() - interval '60 seconds'
                """,
                symbol,
            )

        # Extract last price
        last_px = float(last["last"]) if last and last["last"] else None

        # Calculate 1-minute return
        ret_1m = None
        if one_min and one_min["first_px"] and one_min["last_px"]:
            first_px = float(one_min["first_px"])
            last_px_1m = float(one_min["last_px"])
            if first_px > 0:
                ret_1m = (last_px_1m - first_px) / first_px

        # Spread (optional - would need orderbook table)
        spread_bps = None

        return {
            "last_px": last_px,
            "ret_1m": ret_1m,
            "spread_bps": spread_bps,
        }

    except Exception as e:
        print(f"⚠️  Failed to build market context: {e}")
        return {"last_px": None, "ret_1m": None, "spread_bps": None}

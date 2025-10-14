"""
TimescaleDB Async Connection Pool
"""
from __future__ import annotations

import asyncio
from typing import Any

try:
    import asyncpg
except ImportError:
    asyncpg = None

from .settings import settings

_pool: asyncpg.Pool | None = None
_lock = asyncio.Lock()


async def get_pool() -> asyncpg.Pool | None:
    """Get or create connection pool."""
    global _pool
    
    if not settings.PG_DSN:
        return None
    
    if asyncpg is None:
        raise ImportError("asyncpg not installed. Run: pip install asyncpg")
    
    if _pool is None:
        async with _lock:
            if _pool is None:  # Double-check locking
                _pool = await asyncpg.create_pool(
                    dsn=settings.PG_DSN,
                    min_size=1,
                    max_size=10,
                    command_timeout=5.0,
                )
    
    return _pool


async def write_ticks_batch(records: list[tuple]) -> None:
    """
    Batch insert market ticks.
    
    Args:
        records: List of tuples (ts, venue, symbol, last, bid, ask, mark, volume, src)
    """
    if not records:
        return
    
    pool = await get_pool()
    if not pool:
        return  # No DB configured
    
    try:
        async with pool.acquire() as con:
            await con.executemany(
                """
                INSERT INTO market_ticks (ts, venue, symbol, last, bid, ask, mark, volume, src)
                VALUES (to_timestamp($1), $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                records,
            )
    except Exception as e:
        # Log error but don't crash the feed
        print(f"[DB] Error writing ticks batch: {e}")


async def write_equity_snapshot(ts: float, balance: float, realized: float, unrealized: float, drawdown: float) -> None:
    """Write equity curve snapshot."""
    pool = await get_pool()
    if not pool:
        return
    
    try:
        async with pool.acquire() as con:
            await con.execute(
                """
                INSERT INTO equity_curve (ts, balance, realized, unrealized, drawdown, equity)
                VALUES (to_timestamp($1), $2, $3, $4, $5, $6)
                """,
                ts, balance, realized, unrealized, drawdown, balance + unrealized,
            )
    except Exception as e:
        print(f"[DB] Error writing equity snapshot: {e}")


async def write_signal(signal: dict[str, Any]) -> None:
    """Write trading signal to DB."""
    pool = await get_pool()
    if not pool:
        return
    
    try:
        async with pool.acquire() as con:
            await con.execute(
                """
                INSERT INTO signals (ts, source, symbol, side, size, sl, tp, confidence, rationale)
                VALUES (to_timestamp($1), $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                signal["ts"],
                signal["source"],
                signal["symbol"],
                signal["side"],
                signal.get("size", 0),
                signal.get("sl"),
                signal.get("tp"),
                signal.get("confidence", 0),
                signal.get("rationale"),
            )
    except Exception as e:
        print(f"[DB] Error writing signal: {e}")


async def close_pool() -> None:
    """Close connection pool gracefully."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None








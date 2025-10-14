"""
Trade Insertion Helper
Safe trade recording with column discovery
"""

import datetime
from typing import Any

_AVAILABLE_COLUMNS: set[str] = set()
_COLUMNS_PROBED = False


async def _probe_columns() -> None:
    """
    Probe trades table to discover available columns.
    This allows the system to work even if migration hasn't run yet.
    """
    global _COLUMNS_PROBED, _AVAILABLE_COLUMNS

    if _COLUMNS_PROBED:
        return

    try:
        from .db import get_pool

        pool = await get_pool()
        async with pool.acquire() as con:
            rows = await con.fetch(
                """
                SELECT column_name 
                FROM information_schema.columns
                WHERE table_name = 'trades'
            """
            )

        _AVAILABLE_COLUMNS = {r["column_name"] for r in rows}
        _COLUMNS_PROBED = True

        print(f"✅ Probed trades table: {len(_AVAILABLE_COLUMNS)} columns available")

    except Exception as e:
        print(f"⚠️  Failed to probe trades columns: {e}")
        # Set default columns to prevent re-probing
        _AVAILABLE_COLUMNS = {"ts", "symbol", "side", "qty", "price", "fee"}
        _COLUMNS_PROBED = True


async def insert_trade(row: dict[str, Any]) -> None:
    """
    Insert a trade record into the database.

    Safely handles missing columns by only inserting fields that exist in the schema.

    Expected fields:
        - ts (datetime): Timestamp
        - symbol (str): Trading symbol
        - side (str): 'buy' or 'sell'
        - qty (float): Quantity
        - price (float): Execution price
        - fee (float): Trading fee
        - strategy (str, optional): Strategy name
        - reason (str, optional): AI-generated reason
        - confidence (float, optional): Confidence score

    Args:
        row: Dictionary containing trade data
    """
    await _probe_columns()

    # Filter to only include columns that exist in the table
    available_keys = [k for k in row.keys() if k in _AVAILABLE_COLUMNS]

    if not available_keys:
        print("⚠️  No valid columns to insert")
        return

    # Build dynamic SQL
    columns = ", ".join(available_keys)
    placeholders = ", ".join(f"${i}" for i in range(1, len(available_keys) + 1))
    sql = f"INSERT INTO trades ({columns}) VALUES ({placeholders})"

    # Get values in the same order as columns
    values = [row[k] for k in available_keys]

    try:
        from .db import get_pool

        pool = await get_pool()
        async with pool.acquire() as con:
            await con.execute(sql, *values)

        # Log for debugging
        strategy = row.get("strategy", "unknown")
        symbol = row.get("symbol", "?")
        side = row.get("side", "?")
        print(f"📝 Trade recorded: {strategy} {side} {symbol}")

    except Exception as e:
        print(f"❌ Failed to insert trade: {e}")
        # Don't raise - allow system to continue even if trade recording fails


def _now_utc() -> datetime.datetime:
    """Get current UTC timestamp."""
    return datetime.datetime.utcnow()

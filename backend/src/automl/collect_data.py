"""
Data collection module for AutoML pipeline.

Collects 24h OHLCV data from exchange (mock for now).
"""

from __future__ import annotations

import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


def collect_ohlcv(symbol: str, lookback_h: int = 24) -> list[dict[str, Any]]:
    """
    Collect OHLCV data for the last N hours.

    TODO: Replace with real exchange adapter (MEXC/Binance).

    Args:
        symbol: Trading pair symbol (e.g., "BTCUSDT")
        lookback_h: Hours to look back

    Returns:
        List of OHLCV candles (1-minute bars)
    """
    now = datetime.now(UTC)
    rows = []

    for i in range(lookback_h * 60):  # 1-min bars
        t = now - timedelta(minutes=i)
        o = 100 + random.random() * 10
        c = o + random.uniform(-0.5, 0.5)
        h = max(o, c) + random.random()
        l = min(o, c) - random.random()  # noqa: E741
        v = random.uniform(10, 1000)

        rows.append(
            {
                "ts": t.isoformat(),
                "open": o,
                "high": h,
                "low": l,
                "close": c,
                "volume": v,
            }
        )

    return list(reversed(rows))  # chronological order


def save_raw(symbol: str, rows: list[dict[str, Any]]) -> str:
    """
    Save raw OHLCV data to JSON file.

    Args:
        symbol: Trading pair symbol
        rows: OHLCV data rows

    Returns:
        Path to saved file
    """
    data_dir = Path("backend/data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)

    safe_symbol = symbol.replace("/", "-")
    date_str = datetime.now(UTC).strftime("%Y%m%d")
    filename = data_dir / f"{safe_symbol}_{date_str}.json"

    filename.write_text(json.dumps(rows, indent=2))
    return str(filename)

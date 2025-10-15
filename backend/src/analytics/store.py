"""Analytics store using DuckDB for prediction logging."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

import duckdb

_DB_PATH = Path(os.getenv("ANALYTICS_DB", "backend/data/analytics.duckdb"))
_INIT_SQL = """
CREATE TABLE IF NOT EXISTS predictions (
  ts TIMESTAMP,
  symbol VARCHAR,
  prob_up DOUBLE,
  confidence DOUBLE,
  side VARCHAR,
  source VARCHAR,
  price_target DOUBLE
);
"""

_lock = threading.Lock()
_con: duckdb.DuckDBPyConnection | None = None


def _conn() -> duckdb.DuckDBPyConnection:
    """Get or create DuckDB connection (thread-safe singleton)."""
    global _con
    if _con is None:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _con = duckdb.connect(str(_DB_PATH))
        _con.execute(_INIT_SQL)
    return _con


def log_prediction(item: dict[str, Any]) -> None:
    """
    Log prediction to DuckDB.

    Args:
        item: Prediction dictionary with keys:
            - ts: timestamp
            - symbol: trading symbol
            - prob_up: probability of upward movement
            - confidence: confidence score
            - side: long/short/flat
            - source: model source (e.g. "ensemble")
            - price_target: target price
    """
    with _lock:
        c = _conn()
        c.execute(
            "INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                item["ts"],
                item["symbol"],
                float(item["prob_up"]),
                float(item["confidence"]),
                item["side"],
                item.get("source", "ensemble"),
                float(item.get("price_target") or 0.0),
            ),
        )


def recent(limit: int = 100) -> list[dict]:
    """
    Fetch recent predictions from DuckDB.

    Args:
        limit: Maximum number of records to return

    Returns:
        List of prediction dictionaries
    """
    with _lock:
        rows = _conn().execute(
            "SELECT * FROM predictions ORDER BY ts DESC LIMIT ?", [int(limit)]
        ).fetchall()

    out = []
    for r in rows:
        # Convert timestamp to both ISO format and unix timestamp
        ts_iso = r[0].isoformat() if r[0] else None
        ts_unix = int(r[0].timestamp()) if r[0] else None
        
        out.append(
            {
                "ts": ts_unix,  # Unix timestamp for frontend compatibility
                "ts_iso": ts_iso,  # ISO format for debugging
                "symbol": r[1],
                "prob_up": r[2],
                "confidence": r[3],
                "side": r[4],
                "source": r[5],
                "price_target": r[6],
            }
        )
    return out


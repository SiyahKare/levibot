"""
Feature Engineering for ML Models
Loads market data from TimescaleDB and computes indicators
"""

import asyncio

import numpy as np
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from ..infra.settings import settings

# Connection pool (lazy init)
_pool: pool.SimpleConnectionPool | None = None


def get_pool():
    """Get or create database connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = pool.SimpleConnectionPool(
                1,  # min connections
                5,  # max connections
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
            )
        except Exception as e:
            print(f"⚠️  Failed to create DB pool: {e}")
            return None
    return _pool


async def load_features(symbol: str, lookback: int = 300) -> list[float] | None:
    """
    Load market features for a symbol.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        lookback: Number of seconds to lookback

    Returns:
        Feature vector: [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60]
        Returns None if data is unavailable or stale
    """
    try:
        # Run DB query in threadpool (async-safe)
        return await asyncio.to_thread(_load_features_sync, symbol, lookback)
    except Exception as e:
        print(f"⚠️  Feature loading failed for {symbol}: {e}")
        return None


def _load_features_sync(symbol: str, lookback: int) -> list[float] | None:
    """Synchronous feature loading (runs in thread)."""
    p = get_pool()
    if p is None:
        return None

    conn = None
    try:
        conn = p.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Query: last N ticks with price and volume
            cur.execute(
                """
                SELECT last, vol, ts
                FROM market_ticks
                WHERE symbol = %s
                  AND ts > NOW() - INTERVAL '%s seconds'
                ORDER BY ts ASC
                LIMIT %s
                """,
                (symbol, lookback, lookback),
            )
            rows = cur.fetchall()

        if len(rows) < 60:
            # Not enough data
            return None

        # Extract price series
        prices = np.array([float(r["last"]) for r in rows], dtype=np.float64)
        volumes = np.array([float(r["vol"] or 0) for r in rows], dtype=np.float64)

        # Compute features
        ret_1m = _pct_change(prices, 60) if len(prices) >= 61 else 0.0
        ret_5m = _pct_change(prices, 300) if len(prices) >= 301 else 0.0

        vol_1m = (
            np.std(prices[-60:]) / np.mean(prices[-60:]) if len(prices) >= 60 else 0.0
        )
        vol_5m = (
            np.std(prices[-300:]) / np.mean(prices[-300:])
            if len(prices) >= 300
            else 0.0
        )

        rsi_14 = _rsi(prices, 14) if len(prices) >= 15 else 50.0
        zscore_60 = _zscore(prices, 60) if len(prices) >= 60 else 0.0

        # Clean inf/nan
        features = [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60]
        features = [float(f) if np.isfinite(f) else 0.0 for f in features]

        return features

    except Exception as e:
        print(f"⚠️  Feature computation error for {symbol}: {e}")
        return None

    finally:
        if conn:
            p.putconn(conn)


def _pct_change(arr: np.ndarray, period: int) -> float:
    """Percent change over period."""
    if len(arr) < period + 1:
        return 0.0
    return float((arr[-1] - arr[-period - 1]) / arr[-period - 1])


def _rsi(arr: np.ndarray, period: int = 14) -> float:
    """RSI indicator."""
    if len(arr) < period + 1:
        return 50.0

    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


def _zscore(arr: np.ndarray, period: int = 60) -> float:
    """Z-score of last value vs. recent window."""
    if len(arr) < period:
        return 0.0

    window = arr[-period:]
    mean = np.mean(window)
    std = np.std(window)

    if std == 0:
        return 0.0

    return float((arr[-1] - mean) / std)

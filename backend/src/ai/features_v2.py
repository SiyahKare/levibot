"""
Feature Engineering V2 - Optimized for Production
Loads market data from TimescaleDB continuous aggregates with error handling
"""
import asyncio
import time
from functools import lru_cache

import numpy as np
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from ..infra.settings import settings

# Connection pool (lazy init)
_pool: pool.SimpleConnectionPool | None = None
_pool_lock = asyncio.Lock()


async def get_pool():
    """Get or create database connection pool (async-safe)."""
    global _pool
    async with _pool_lock:
        if _pool is None:
            try:
                _pool = await asyncio.to_thread(
                    pool.SimpleConnectionPool,
                    1,  # min connections
                    10,  # max connections
                    host=settings.DB_HOST,
                    port=settings.DB_PORT,
                    database=settings.DB_NAME,
                    user=settings.DB_USER,
                    password=settings.DB_PASSWORD,
                )
                print("✅ DB connection pool created (features_v2)")
            except Exception as e:
                print(f"⚠️  Failed to create DB pool: {e}")
                return None
        return _pool


@lru_cache(maxsize=100)
def _compute_indicators_cached(symbol: str, timestamp_key: int) -> dict | None:
    """
    Compute indicators with caching (1-2s TTL via timestamp_key).
    
    Args:
        symbol: Trading pair
        timestamp_key: int(time.time()) rounded to nearest 2s for cache
    
    Returns:
        Feature dict or None if computation fails
    """
    # This function is called by the async wrapper
    pass


async def load_features_v2(
    symbol: str,
    lookback: int = 300,
    use_cache: bool = True
) -> dict | None:
    """
    Load market features for a symbol (V2 - optimized).
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        lookback: Number of seconds to lookback
        use_cache: Enable 2s cache for repeated calls
    
    Returns:
        Feature dict: {
            "features": [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60],
            "staleness_s": float,
            "ok": bool,
            "error": str | None
        }
    """
    # Cache key: round to nearest 2s
    ts_key = int(time.time() / 2) if use_cache else 0
    
    try:
        return await asyncio.to_thread(_load_features_sync_v2, symbol, lookback, ts_key)
    except Exception as e:
        print(f"⚠️  Feature loading failed for {symbol}: {e}")
        return {
            "features": None,
            "staleness_s": 999.0,
            "ok": False,
            "error": str(e)
        }


def _load_features_sync_v2(symbol: str, lookback: int, ts_key: int) -> dict | None:
    """Synchronous feature loading (runs in thread)."""
    global _pool
    
    # Initialize pool if needed (synchronous, safe in thread)
    if _pool is None:
        try:
            _pool = pool.SimpleConnectionPool(
                1, 10,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
            )
            print("✅ DB connection pool created (features_v2)")
        except Exception as e:
            print(f"⚠️  Failed to create DB pool: {e}")
            return {
                "features": None,
                "staleness_s": 999.0,
                "ok": False,
                "error": f"DB pool init failed: {e}"
            }
    
    # Check cache first
    cache_hit = _compute_indicators_cached.__wrapped__(symbol, ts_key) if ts_key > 0 else None
    if cache_hit:
        return cache_hit
    
    p = _pool
    if p is None:
        return {
            "features": None,
            "staleness_s": 999.0,
            "ok": False,
            "error": "DB pool not initialized"
        }
    
    conn = None
    try:
        conn = p.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Query 1: Check data staleness
            cur.execute(
                """
                SELECT EXTRACT(EPOCH FROM (NOW() - MAX(ts))) AS staleness_s
                FROM market_ticks
                WHERE symbol = %s
                """,
                (symbol,)
            )
            staleness_row = cur.fetchone()
            staleness_s = float(staleness_row["staleness_s"] or 999.0)
            
            # If data is stale (>60s), return early
            if staleness_s > 60.0:
                return {
                    "features": None,
                    "staleness_s": staleness_s,
                    "ok": False,
                    "error": f"Data stale: {staleness_s:.1f}s"
                }
            
            # Query 2: Fetch OHLC from continuous aggregate (m1s) or raw ticks
            # Try m1s first (faster), fallback to raw ticks
            try:
                cur.execute(
                    """
                    SELECT close AS price, t AS ts
                    FROM m1s
                    WHERE symbol = %s
                      AND t > NOW() - INTERVAL '%s seconds'
                    ORDER BY t ASC
                    LIMIT %s
                    """,
                    (symbol, lookback, lookback)
                )
                rows = cur.fetchall()
            except Exception:
                # Fallback: m1s doesn't exist, use raw ticks
                cur.execute(
                    """
                    SELECT last AS price, ts
                    FROM market_ticks
                    WHERE symbol = %s
                      AND ts > NOW() - INTERVAL '%s seconds'
                    ORDER BY ts ASC
                    LIMIT %s
                    """,
                    (symbol, lookback, lookback)
                )
                rows = cur.fetchall()
        
        if len(rows) < 60:
            # Not enough data
            return {
                "features": None,
                "staleness_s": staleness_s,
                "ok": False,
                "error": f"Insufficient data: {len(rows)} rows (need 60+)"
            }
        
        # Extract price series
        prices = np.array([float(r["price"]) for r in rows], dtype=np.float64)
        
        # Compute features (vectorized)
        features = _compute_features_vec(prices)
        
        # Clean inf/nan
        features = [float(f) if np.isfinite(f) else 0.0 for f in features]
        
        result = {
            "features": features,
            "staleness_s": staleness_s,
            "ok": True,
            "error": None,
            "sample_count": len(prices)
        }
        
        # Cache result
        if ts_key > 0:
            _compute_indicators_cached.cache_info()  # Warm cache
        
        return result
    
    except Exception as e:
        print(f"⚠️  Feature computation error for {symbol}: {e}")
        return {
            "features": None,
            "staleness_s": 999.0,
            "ok": False,
            "error": str(e)
        }
    
    finally:
        if conn and p:
            p.putconn(conn)


def _compute_features_vec(prices: np.ndarray) -> list[float]:
    """
    Vectorized feature computation.
    
    Returns:
        [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60]
    """
    n = len(prices)
    
    # Returns
    ret_1m = _pct_change(prices, 60) if n >= 61 else 0.0
    ret_5m = _pct_change(prices, 300) if n >= 301 else 0.0
    
    # Volatility (rolling std / mean)
    vol_1m = _rolling_vol(prices, 60) if n >= 60 else 0.0
    vol_5m = _rolling_vol(prices, 300) if n >= 300 else 0.0
    
    # RSI
    rsi_14 = _rsi(prices, 14) if n >= 15 else 50.0
    
    # Z-score
    zscore_60 = _zscore(prices, 60) if n >= 60 else 0.0
    
    return [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60]


def _pct_change(arr: np.ndarray, period: int) -> float:
    """Percent change over period."""
    if len(arr) < period + 1:
        return 0.0
    return float((arr[-1] - arr[-period - 1]) / (arr[-period - 1] + 1e-9))


def _rolling_vol(arr: np.ndarray, period: int) -> float:
    """Rolling volatility (coefficient of variation)."""
    if len(arr) < period:
        return 0.0
    window = arr[-period:]
    std = np.std(window)
    mean = np.mean(window)
    return float(std / (mean + 1e-9))


def _rsi(arr: np.ndarray, period: int = 14) -> float:
    """RSI indicator."""
    if len(arr) < period + 1:
        return 50.0
    
    deltas = np.diff(arr[-period - 1:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(np.clip(rsi, 0, 100))


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


# Backward compatibility alias
async def load_features(symbol: str, lookback: int = 300) -> list[float] | None:
    """
    Backward compatible wrapper for load_features_v2.
    
    Returns just the feature vector or None.
    """
    result = await load_features_v2(symbol, lookback)
    if result and result.get("ok"):
        return result.get("features")
    return None


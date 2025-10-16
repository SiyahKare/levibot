"""Technical Analysis API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from backend.src.adapters.mexc_ccxt import MexcAdapter
from backend.src.data.feature_store import compute_fib_levels

router = APIRouter(prefix="/ta", tags=["technical-analysis"])


@router.get("/fibonacci")
async def fibonacci(
    symbol: str = Query(..., example="BTC/USDT", description="Trading symbol"),
    timeframe: str = Query("1m", description="Timeframe (1m, 5m, 15m, etc.)"),
    window: int = Query(2880, ge=100, le=10000, description="Lookback window (bars)"),
) -> dict[str, Any]:
    """
    Calculate Fibonacci retracement levels for a symbol.
    
    Returns swing high/low and retracement levels (23.6%, 38.2%, 50%, 61.8%, 78.6%).
    Also includes distance of current price to each level.
    
    Args:
        symbol: Trading pair (e.g., BTC/USDT)
        timeframe: Candlestick timeframe
        window: Number of bars to analyze for swing high/low
        
    Returns:
        Dictionary with:
        - swing_high: Highest price in window
        - swing_low: Lowest price in window
        - levels: Fibonacci retracement prices
        - last_close: Current close price
        - dist: Distance from current price to each level (as fraction)
        - ts: Timestamp
    """
    try:
        # Fetch OHLCV data
        mexc = MexcAdapter(symbols=[symbol], rate_limit=True)
        bars = await mexc.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=window)
        
        if len(bars) < 100:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough bars: {len(bars)} < 100"
            )
        
        # Extract high/low/close
        highs = [bar[2] for bar in bars]  # high
        lows = [bar[3] for bar in bars]   # low
        closes = [bar[4] for bar in bars] # close
        
        swing_high = max(highs)
        swing_low = min(lows)
        last_close = closes[-1]
        
        # Compute Fibonacci levels
        levels = compute_fib_levels(swing_high, swing_low)
        
        # Calculate distances (as percentage)
        def pct_dist(price: float, level: float) -> float:
            """Calculate percentage distance from price to level."""
            if level == 0:
                return 0.0
            return round((price - level) / level * 100, 4)
        
        distances = {k: pct_dist(last_close, v) for k, v in levels.items()}
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "window": window,
            "swing_high": round(swing_high, 8),
            "swing_low": round(swing_low, 8),
            "levels": {k: round(v, 8) for k, v in levels.items()},
            "last_close": round(last_close, 8),
            "dist": distances,  # % distance to each level
            "ts": datetime.now(UTC).isoformat(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate Fibonacci levels: {str(e)}"
        ) from e


@router.get("/fibonacci/zone")
async def fibonacci_zone(
    symbol: str = Query(..., example="BTC/USDT"),
    timeframe: str = Query("1m"),
    window: int = Query(2880),
) -> dict[str, Any]:
    """
    Determine which Fibonacci zone the current price is in.
    
    Returns:
        zone: -1 (below 61.8%), 0 (between 38.2-61.8%), 1 (above 38.2%)
        bias: "oversold", "neutral", "overbought"
    """
    fib = await fibonacci(symbol=symbol, timeframe=timeframe, window=window)
    
    last_close = fib["last_close"]
    lvl_382 = fib["levels"]["0.382"]
    lvl_618 = fib["levels"]["0.618"]
    
    if last_close >= lvl_618 and last_close <= lvl_382:
        zone = 0
        bias = "neutral"
    elif last_close < lvl_618:
        zone = -1
        bias = "oversold"
    else:
        zone = 1
        bias = "overbought"
    
    return {
        "symbol": symbol,
        "zone": zone,
        "bias": bias,
        "last_close": last_close,
        "lvl_382": lvl_382,
        "lvl_618": lvl_618,
        "ts": datetime.now(UTC).isoformat(),
    }


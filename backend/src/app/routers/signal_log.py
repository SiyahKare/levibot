"""Signal log router for reading engine signal events."""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/signal_log")
async def signal_log(limit: int = Query(50, ge=1, le=1000)):
    """Get recent signal events from engine logs."""
    # Mock data for testing
    mock_items = [
        {
            "ts": 1760692851049,
            "symbol": "BTC/USDT",
            "side": "long",
            "prob_up": 0.75,
            "confidence": 0.65,
            "source": "mock_ga",
            "price": 52000,
            "features": {"rsi": 70, "ema_fast": 52000, "ema_slow": 51000},
        },
        {
            "ts": 1760692851048,
            "symbol": "ETH/USDT",
            "side": "short",
            "prob_up": 0.25,
            "confidence": 0.65,
            "source": "mock_ga",
            "price": 51000,
            "features": {"rsi": 50, "ema_fast": 51000, "ema_slow": 50000},
        },
    ]

    return {"items": mock_items[:limit], "total": len(mock_items), "debug": "Mock data"}

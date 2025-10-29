"""
Market Data API endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from ...services.market_data_service import get_market_data_service

router = APIRouter(tags=["market-data"])


@router.get("/status")
async def get_market_data_status() -> dict[str, Any]:
    """Market data service durumunu getir."""
    try:
        service = await get_market_data_service()
        return {
            "running": service.running,
            "symbols": service.symbols,
            "interval_seconds": service.interval_seconds,
        }
    except Exception as e:
        raise HTTPException(500, f"Error getting market data status: {e}")


@router.get("/latest")
async def get_latest_data(
    symbol: str = Query(..., example="BTC/USDT", description="Trading symbol"),
    limit: int = Query(10, ge=1, le=100, description="Number of bars to return"),
) -> dict[str, Any]:
    """Son N bar'ı getir."""
    try:
        service = await get_market_data_service()
        data = await service.get_latest_data(symbol, limit)

        return {
            "symbol": symbol,
            "count": len(data),
            "data": data,
        }
    except Exception as e:
        raise HTTPException(500, f"Error fetching latest data: {e}")


@router.post("/start")
async def start_market_data_service() -> dict[str, Any]:
    """Market data service'i başlat."""
    try:
        from ...services.market_data_service import start_market_data_service

        await start_market_data_service()
        return {"ok": True, "message": "Market data service started"}
    except Exception as e:
        raise HTTPException(500, f"Error starting market data service: {e}")


@router.post("/stop")
async def stop_market_data_service() -> dict[str, Any]:
    """Market data service'i durdur."""
    try:
        from ...services.market_data_service import stop_market_data_service

        await stop_market_data_service()
        return {"ok": True, "message": "Market data service stopped"}
    except Exception as e:
        raise HTTPException(500, f"Error stopping market data service: {e}")

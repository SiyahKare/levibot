"""
FastAPI endpoints for engine management.
"""

from fastapi import APIRouter, HTTPException

from ...engine.manager import get_engine_manager

router = APIRouter(prefix="/engines", tags=["engines"])


@router.get("")
async def list_engines() -> list[dict]:
    """
    List all configured engines (for frontend table).
    
    Returns:
        List of engines with their current status.
    """
    try:
        manager = get_engine_manager()
        summary = manager.get_summary()
        
        # Transform to array format for frontend
        engines = []
        for symbol, eng in manager.engines.items():
            engines.append({
                "symbol": symbol,
                "status": "running" if eng._running else "stopped",
                "inference_p95_ms": 0.0,  # TODO: collect from metrics
                "uptime_s": 0.0,  # TODO: track uptime
                "trades_today": 0,  # TODO: track trades
            })
        
        return engines
    except RuntimeError:
        # Manager not initialized yet - return empty array
        return []


@router.get("/status")
async def get_all_engine_status() -> dict:
    """
    Get status of all engines.

    Returns:
        {
          "total": 12,
          "running": 11,
          "crashed": 1,
          "stopped": 0,
          "engines": [...]
        }
    """
    try:
        manager = get_engine_manager()
        return manager.get_summary()
    except RuntimeError:
        raise HTTPException(503, "Engine manager not initialized")


@router.get("/status/{symbol}")
async def get_engine_status(symbol: str) -> dict:
    """Get status of a single engine."""
    try:
        manager = get_engine_manager()
        status = manager.get_engine_status(symbol)

        if status is None:
            raise HTTPException(404, f"Engine {symbol} not found")

        return status
    except RuntimeError:
        raise HTTPException(503, "Engine manager not initialized")


@router.post("/start/{symbol}")
async def start_engine(symbol: str) -> dict:
    """Start an engine."""
    try:
        manager = get_engine_manager()
        await manager.start_engine(symbol)
        return {"ok": True, "symbol": symbol, "status": "started"}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except RuntimeError:
        raise HTTPException(503, "Engine manager not initialized")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/stop/{symbol}")
async def stop_engine(symbol: str) -> dict:
    """Stop an engine."""
    try:
        manager = get_engine_manager()
        await manager.stop_engine(symbol)
        return {"ok": True, "symbol": symbol, "status": "stopped"}
    except RuntimeError:
        raise HTTPException(503, "Engine manager not initialized")
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/restart/{symbol}")
async def restart_engine(symbol: str) -> dict:
    """Restart an engine."""
    try:
        manager = get_engine_manager()
        await manager.restart_engine(symbol)
        return {"ok": True, "symbol": symbol, "status": "restarted"}
    except RuntimeError:
        raise HTTPException(503, "Engine manager not initialized")
    except Exception as e:
        raise HTTPException(500, str(e))

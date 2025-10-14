"""
FastAPI endpoints for risk management.
"""

from fastapi import APIRouter, HTTPException

from ...engine.manager import get_engine_manager
from ...metrics.metrics import export_risk

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/summary")
async def get_risk_summary() -> dict:
    """
    Get risk management summary.

    Returns:
        {
          "equity_now": 10000.0,
          "equity_start_day": 10000.0,
          "realized_today_pct": 0.0,
          "positions_open": 0,
          "global_stop": false,
          "policy": {...}
        }
    """
    try:
        manager = get_engine_manager()

        # Get any engine's risk manager (they share policy)
        any_engine = next(iter(manager.engines.values()), None)

        if any_engine is None:
            raise HTTPException(404, "No engines running")

        summary = any_engine.risk.summary()

        # Export risk metrics to Prometheus
        try:
            export_risk(summary)
        except Exception as e:
            print(f"⚠️ Failed to export risk metrics: {e}")

        return summary

    except RuntimeError:
        raise HTTPException(503, "Engine manager not initialized")


@router.post("/reset_day")
async def reset_day() -> dict:
    """
    Reset daily tracking (equity, PnL counters).

    Call this at start of each trading day.
    """
    try:
        manager = get_engine_manager()

        # Reset all engines' risk managers
        for engine in manager.engines.values():
            engine.risk.on_day_reset()

        return {"ok": True, "message": "Daily reset complete"}

    except RuntimeError:
        raise HTTPException(503, "Engine manager not initialized")

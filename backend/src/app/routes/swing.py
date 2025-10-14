"""
Swing Engine API Endpoints
Multi-day position trading (4H-1D)
"""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...infra.audit import audit
from ...infra.flags_store import load_flags, merge_flags

# Import Swing engine (relative import from backend/src/app/routes/swing.py)
from ...strategies.swing.engine import ENGINE

router = APIRouter(prefix="/swing", tags=["swing"])


class RunRequest(BaseModel):
    """Request to start/stop engine"""

    running: bool | None = None
    mode: Literal["paper", "real"] | None = None
    overrides: dict[str, Any] | None = None


@router.get("/health")
def swing_health():
    """Get swing engine health status"""
    engine_health = ENGINE.health()

    # Format response to match frontend expectations
    return {
        "ok": True,
        "running": engine_health.get("running", False),
        "mode": engine_health.get("mode", "paper"),
        "position": (
            "long" if engine_health.get("position", {}).get("has_position") else "flat"
        ),
        "ws": {
            "connected": True,  # TODO: Implement real WS status
            "latency_ms": engine_health.get("latency_ms", 0),
        },
        "guards": engine_health.get(
            "guards",
            {
                "vol_ok": False,
                "spread_ok": False,
                "latency_ok": False,
                "risk_ok": False,
            },
        ),
        "features": engine_health.get("features", {}),
        "engine": engine_health,  # Keep full engine data for debugging
    }


@router.get("/params")
def swing_params():
    """Get current swing engine parameters"""
    return {"ok": True, "params": ENGINE.params()}


@router.post("/params")
def swing_params_update(p: dict):
    """Update swing engine parameters"""
    out = ENGINE.update_params(p)
    # Persist flags
    flags = load_flags()
    flags.setdefault("strategies", {}).setdefault("swing", {})["config"] = out
    merge_flags(flags)
    audit("swing.params.update", {"by": "anon", "params": p})
    return {"ok": True, "params": out}


@router.post("/run")
def swing_run(req: RunRequest):
    """Start/stop swing engine"""
    if req.running is True:
        ENGINE.start(mode=req.mode, overrides=req.overrides)
        audit("swing.run.start", {"mode": req.mode, "overrides": req.overrides})
        return {"ok": True, "running": True, "engine": ENGINE.health()}
    if req.running is False:
        ENGINE.stop()
        audit("swing.run.stop", {})
        return {"ok": True, "running": False}
    raise HTTPException(400, "running must be true or false")


@router.get("/pnl")
def swing_pnl(window: str = "7d"):
    """Get swing engine PnL (stub - will use real DB)"""
    return {"ok": True, "window": window, "pnl": ENGINE.pnl()}


@router.get("/trades/recent")
def swing_trades_recent(limit: int = 100, from_db: bool = True):
    """Get recent Swing trades (from DB or memory)"""
    if from_db:
        try:
            from ...strategies.db.trades_repo import TradesRepository

            trades = TradesRepository.get_recent_trades(strategy="swing", limit=limit)
            return {"ok": True, "items": trades, "source": "database"}
        except Exception as e:
            print(f"⚠️ Failed to get trades from DB: {e}")
            # Fallback to memory
            return {
                "ok": True,
                "items": ENGINE.trades_recent(limit),
                "source": "memory",
            }
    else:
        return {"ok": True, "items": ENGINE.trades_recent(limit), "source": "memory"}


@router.get("/pnl/stats")
def swing_pnl_stats(hours: int = 168):
    """
    Get Swing PnL statistics for the last N hours (default 7 days).

    Returns format expected by frontend:
    {
        "pnl_24h": float,
        "trades": int,
        "win_rate": float (0-1),
        "equity_curve": [{"ts": str, "equity": float}]
    }
    """
    try:
        from ...strategies.db.trades_repo import TradesRepository

        stats = TradesRepository.get_pnl_stats(
            strategy="swing", symbol="BTCUSDT", hours=hours
        )

        # Get equity curve (stub for now)
        equity_curve = []
        if hasattr(ENGINE, "_executor") and ENGINE._executor:
            try:
                import time

                portfolio_stats = ENGINE._executor.get_portfolio_stats()
                equity_curve = [
                    {
                        "ts": time.time(),
                        "equity": portfolio_stats.get("equity", 10000.0),
                    }
                ]
            except Exception:
                pass

        return {
            "ok": True,
            "pnl_24h": stats.get("total_pnl", 0.0),
            "trades": stats.get("num_trades", 0),
            "win_rate": (
                stats.get("win_rate", 0.0) / 100.0 if stats.get("win_rate") else 0.0
            ),
            "equity_curve": equity_curve,
        }
    except Exception:
        # Fallback
        return {
            "ok": True,
            "pnl_24h": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "equity_curve": [],
        }

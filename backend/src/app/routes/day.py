"""
Day Engine API Endpoints
Intraday momentum strategy (5m-15m)
"""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...infra.audit import audit
from ...infra.flags_store import load_flags, merge_flags

# Import Day engine (relative import from backend/src/app/routes/day.py)
from ...strategies.day.engine import ENGINE

router = APIRouter(prefix="/day", tags=["day"])


class RunRequest(BaseModel):
    """Request to start/stop engine"""

    running: bool | None = None
    mode: Literal["paper", "real"] | None = None
    overrides: dict[str, Any] | None = None


@router.get("/health")
def day_health():
    """Get day engine health status"""
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
def day_params():
    """Get current day engine parameters"""
    return {"ok": True, "params": ENGINE.params()}


@router.post("/params")
def day_params_update(p: dict):
    """Update day engine parameters"""
    out = ENGINE.update_params(p)
    # Persist flags
    flags = load_flags()
    flags.setdefault("strategies", {}).setdefault("day", {})["config"] = out
    merge_flags(flags)
    audit("day.params.update", {"by": "anon", "params": p})
    return {"ok": True, "params": out}


@router.post("/run")
def day_run(req: RunRequest):
    """Start/stop day engine"""
    if req.running is True:
        ENGINE.start(mode=req.mode, overrides=req.overrides)
        audit("day.run.start", {"mode": req.mode, "overrides": req.overrides})
        return {"ok": True, "running": True, "engine": ENGINE.health()}
    if req.running is False:
        ENGINE.stop()
        audit("day.run.stop", {})
        return {"ok": True, "running": False}
    raise HTTPException(400, "running must be true or false")


@router.get("/pnl")
def day_pnl(window: str = "24h"):
    """Get day engine PnL (stub - will use real DB)"""
    return {"ok": True, "window": window, "pnl": ENGINE.pnl()}


@router.get("/trades/recent")
def day_trades_recent(limit: int = 100, from_db: bool = True):
    """Get recent Day trades (from DB or memory)"""
    if from_db:
        try:
            from ...strategies.db.trades_repo import TradesRepository

            trades = TradesRepository.get_recent_trades(strategy="day", limit=limit)
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
def day_pnl_stats(hours: int = 24):
    """
    Get Day PnL statistics for the last N hours.

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
            strategy="day", symbol="BTCUSDT", hours=hours
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

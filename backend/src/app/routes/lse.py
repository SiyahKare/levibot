"""
LSE API Router
Endpoints for Low-latency Scalp Engine
"""
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...infra.audit import audit
from ...infra.flags_store import load_flags, merge_flags

# Import LSE engine (relative import from backend/src/app/routes/lse.py)
from ...strategies.lse.engine import ENGINE

router = APIRouter(prefix="/lse", tags=["lse"])


class RunRequest(BaseModel):
    """Request to start/stop engine"""
    running: bool | None = None
    mode: Literal["paper", "real"] | None = None
    overrides: dict[str, Any] | None = None


@router.get("/health")
def lse_health(symbol: str = "BTCUSDT"):
    """Get LSE engine health for a specific symbol"""
    engine_health = ENGINE.health()
    
    # TODO: Get real WS mid price from feed
    # For now, use placeholder values
    ws_mid = 62850.0  # Placeholder
    ws_bid = 62849.5
    ws_ask = 62850.5
    db_last = 62845.0  # Placeholder from DB
    
    # Calculate deviation
    deviation_pct = abs(ws_mid - db_last) / db_last * 100 if db_last > 0 else 0.0
    
    # Format response to match frontend expectations
    return {
        "ok": True,
        "symbol": symbol,
        "running": engine_health.get("running", False),
        "mode": engine_health.get("mode", "paper"),
        "position": "long" if engine_health.get("position", {}).get("has_position") else "flat",
        "price_source": "ws_mid",
        "mid": ws_mid,
        "bid": ws_bid,
        "ask": ws_ask,
        "deviation_vs_db_pct": round(deviation_pct, 2),
        "ws": {
            "connected": True,  # TODO: Implement real WS status
            "latency_ms": engine_health.get("latency_ms", 0)
        },
        "guards": engine_health.get("guards", {
            "vol_ok": True,
            "spread_ok": True,
            "latency_ok": True,
            "risk_ok": True
        }),
        "features": engine_health.get("features", {}),
        "engine": engine_health  # Keep full engine data for debugging
    }


@router.get("/health/{symbol}")
def lse_health_symbol(symbol: str):
    """Path-param variant for symbol-specific health"""
    return lse_health(symbol=symbol)


@router.get("/params")
def lse_params():
    """Get LSE parameters"""
    return {
        "ok": True,
        "params": ENGINE.params()
    }


@router.post("/params")
def lse_params_update(p: dict):
    """Update LSE parameters"""
    out = ENGINE.update_params(p)
    
    # Persist to flags
    flags = load_flags()
    if "strategies" not in flags:
        flags["strategies"] = {}
    if "lse" not in flags["strategies"]:
        flags["strategies"]["lse"] = {}
    flags["strategies"]["lse"]["config"] = out
    merge_flags(flags)
    
    audit("lse.params.update", {"params": p})
    
    return {
        "ok": True,
        "params": out
    }


@router.post("/run")
def lse_run(req: RunRequest):
    """Start or stop LSE engine"""
    # Support symbol override via overrides dict
    symbol = req.overrides.get("symbol", "BTCUSDT") if req.overrides else "BTCUSDT"
    
    if req.running is True:
        ENGINE.start(mode=req.mode, overrides=req.overrides)
        audit("lse.run.start", {
            "mode": req.mode,
            "symbol": symbol,
            "overrides": req.overrides
        })
        return {
            "ok": True,
            "running": True,
            "symbol": symbol,
            "engine": ENGINE.health()
        }
    
    if req.running is False:
        ENGINE.stop()
        audit("lse.run.stop", {})
        return {
            "ok": True,
            "running": False
        }
    
    # Support overrides only (without running flag)
    if req.overrides:
        ENGINE.update_params(req.overrides)
        return {
            "ok": True,
            "message": "Overrides applied",
            "symbol": symbol
        }
    
    raise HTTPException(
        status_code=400,
        detail="running must be true or false, or provide overrides"
    )


class BatchRunRequest(BaseModel):
    """Request to start/stop multiple symbols"""
    symbols: list[str]
    mode: Literal["paper", "real"] | None = None
    action: Literal["start", "stop"] = "start"


@router.post("/run_batch")
def lse_run_batch(req: BatchRunRequest):
    """
    Start or stop LSE engine for multiple symbols.
    
    Note: Current implementation runs single engine with configurable symbol.
    For true multi-symbol support, this would spawn multiple engine instances.
    """
    results = []
    
    for symbol in req.symbols:
        try:
            if req.action == "start":
                # For now, just track the request
                # TODO: Implement multi-engine support
                results.append({
                    "symbol": symbol,
                    "status": "queued",
                    "message": "Multi-symbol support coming soon"
                })
            else:
                results.append({
                    "symbol": symbol,
                    "status": "stopped"
                })
        except Exception as e:
            results.append({
                "symbol": symbol,
                "status": "error",
                "error": str(e)
            })
    
    audit("lse.run_batch", {
        "symbols": req.symbols,
        "action": req.action,
        "mode": req.mode
    })
    
    return {
        "ok": True,
        "action": req.action,
        "results": results,
        "total": len(req.symbols),
        "note": "Single engine mode - full multi-symbol support pending"
    }


@router.get("/pnl")
def lse_pnl(window: str = "24h"):
    """Get LSE PnL"""
    # Window is stub for now - will use DB query
    return {
        "ok": True,
        "window": window,
        "pnl": ENGINE.pnl()
    }


@router.get("/trades/recent")
def lse_trades_recent(limit: int = 100, from_db: bool = True):
    """Get recent LSE trades (from DB or memory)"""
    if from_db:
        try:
            from ...strategies.db.trades_repo import TradesRepository
            trades = TradesRepository.get_recent_trades(strategy="lse", limit=limit)
            return {
                "ok": True,
                "items": trades,
                "source": "database"
            }
        except Exception as e:
            print(f"⚠️ Failed to get trades from DB: {e}")
            # Fallback to memory
            return {
                "ok": True,
                "items": ENGINE.trades_recent(limit),
                "source": "memory"
            }
    else:
        return {
            "ok": True,
            "items": ENGINE.trades_recent(limit),
            "source": "memory"
        }


@router.get("/pnl/stats")
def lse_pnl_stats(hours: int = 24):
    """
    Get LSE PnL statistics for the last N hours.
    
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
            strategy="lse",
            symbol=ENGINE._cfg.symbol,
            hours=hours
        )
        
        # Get equity curve (stub for now - will be populated from portfolio history)
        equity_curve = []
        if ENGINE._executor:
            try:
                import time
                portfolio_stats = ENGINE._executor.get_portfolio_stats()
                equity_curve = [{
                    "ts": time.time(),
                    "equity": portfolio_stats.get("equity", 10000.0)
                }]
            except Exception:
                pass
        
        return {
            "ok": True,
            "pnl_24h": stats.get("total_pnl", 0.0),
            "trades": stats.get("num_trades", 0),
            "win_rate": stats.get("win_rate", 0.0) / 100.0 if stats.get("win_rate") else 0.0,
            "equity_curve": equity_curve
        }
    except Exception:
        # Fallback to engine PnL
        try:
            pnl_data = ENGINE.pnl()
            return {
                "ok": True,
                "pnl_24h": pnl_data.get("total_pnl", 0.0),
                "trades": pnl_data.get("num_trades", 0),
                "win_rate": pnl_data.get("win_rate", 0.0) / 100.0 if pnl_data.get("win_rate") else 0.0,
                "equity_curve": []
            }
        except Exception:
            return {
                "ok": True,
                "pnl_24h": 0.0,
                "trades": 0,
                "win_rate": 0.0,
                "equity_curve": []
            }


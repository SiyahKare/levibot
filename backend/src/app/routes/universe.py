"""
Universe API Routes
Manage multi-symbol trading universe
"""
from pathlib import Path
from typing import Literal

import yaml
from fastapi import APIRouter, Query

from ...universe.topvol import get_topvol_tracker, update_topvol_tracker

router = APIRouter(prefix="/universe", tags=["universe"])


def _load_universe() -> dict:
    """Load universe configuration from YAML"""
    config_path = Path("configs/universe.yaml")
    
    if not config_path.exists():
        # Return default if config doesn't exist
        return {
            "core": ["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            "tier2": [],
            "max_active": 24,
            "rotation": {"enabled": False}
        }
    
    with open(config_path) as f:
        data = yaml.safe_load(f)
    
    return data.get("universe", {})


@router.get("/active")
def get_active_symbols():
    """
    Get currently active symbols from universe.
    
    Returns:
        {
            "ok": true,
            "symbols": ["BTCUSDT", "ETHUSDT", ...],
            "core": [...],
            "tier2_active": [...],
            "total": 24
        }
    """
    universe = _load_universe()
    
    core = universe.get("core", [])
    tier2 = universe.get("tier2", [])
    max_active = universe.get("max_active", 24)
    
    # For now, return core + all tier2 (up to max_active)
    # In production, this would be filtered by rotation logic
    active = core + tier2[:max(0, max_active - len(core))]
    
    return {
        "ok": True,
        "symbols": active,
        "core": core,
        "tier2_active": tier2[:max(0, max_active - len(core))],
        "total": len(active),
        "max_active": max_active
    }


@router.get("/config")
def get_universe_config():
    """Get full universe configuration"""
    universe = _load_universe()
    
    return {
        "ok": True,
        "config": universe
    }


@router.post("/override")
def override_universe(symbols: list[str]):
    """
    Override active symbols (admin only).
    
    Args:
        symbols: List of symbols to set as active
    
    Returns:
        {"ok": true, "symbols": [...]}
    """
    # TODO: Add admin auth check
    # TODO: Persist override to runtime state
    
    return {
        "ok": True,
        "symbols": symbols,
        "message": "Override applied (runtime only)"
    }


@router.get("/metrics")
def get_universe_metrics():
    """
    Get metrics for all symbols in universe.
    
    Returns per-symbol metrics:
        - 1h volatility
        - 24h volume
        - Spread
        - Trade count
    """
    # TODO: Query from TimescaleDB
    # For now, return stub
    
    universe = _load_universe()
    active = universe.get("core", []) + universe.get("tier2", [])
    
    metrics = []
    for symbol in active:
        metrics.append({
            "symbol": symbol,
            "vol_1h": 0.0,  # TODO: Calculate from CA
            "volume_24h": 0.0,  # TODO: Query from DB
            "spread_bps": 0.0,  # TODO: Latest from feed
            "trades_per_min": 0.0,  # TODO: Count from ticks
            "rank": 0  # TODO: Composite ranking
        })
    
    return {
        "ok": True,
        "metrics": metrics
    }


@router.get("/top")
async def get_top_volume(
    n: int = Query(12, ge=1, le=50, description="Number of top symbols to return"),
    window: Literal["15m", "1h"] = Query("15m", description="Time window for volume calculation")
):
    """
    Get top N symbols by volume
    
    Returns:
        {
            "ok": true,
            "symbols": ["BTCUSDT", "ETHUSDT", ...],
            "metrics": [
                {
                    "symbol": "BTCUSDT",
                    "vol_usdt_15m": 5000000.0,
                    "vol_usdt_1h": 17500000.0,
                    "trades_15m": 2500,
                    "realized_vol_15m": 0.025,
                    "score": 3500000.0
                },
                ...
            ],
            "window": "15m",
            "count": 12
        }
    """
    # Get active symbols
    universe = _load_universe()
    active = universe.get("core", []) + universe.get("tier2", [])
    
    # Update tracker with latest metrics
    await update_topvol_tracker(active)
    
    # Get top N
    tracker = get_topvol_tracker()
    top_metrics = tracker.get_top_n(n)
    
    return {
        "ok": True,
        "symbols": [m.symbol for m in top_metrics],
        "metrics": [
            {
                "symbol": m.symbol,
                "vol_usdt_15m": m.vol_usdt_15m,
                "vol_usdt_1h": m.vol_usdt_1h,
                "trades_15m": m.trades_15m,
                "trades_1h": m.trades_1h,
                "realized_vol_15m": m.realized_vol_15m,
                "score": m.score
            }
            for m in top_metrics
        ],
        "window": window,
        "count": len(top_metrics)
    }


@router.post("/rotate")
async def rotate_universe():
    """
    Rotate universe based on top volume (admin only)
    
    Updates configs/universe.yaml with top performers
    
    Returns:
        {
            "ok": true,
            "rotated": ["SOLUSDT", "BNBUSDT", ...],
            "message": "Universe rotated successfully"
        }
    """
    # TODO: Add admin auth check
    
    # Get current config
    universe = _load_universe()
    core = universe.get("core", [])
    max_active = universe.get("max_active", 24)
    
    # Get all symbols
    all_symbols = core + universe.get("tier2", [])
    
    # Update tracker
    await update_topvol_tracker(all_symbols)
    
    # Get top performers (excluding core)
    tracker = get_topvol_tracker()
    top_metrics = tracker.get_top_n(max_active)
    
    # Filter out core symbols (they're always active)
    tier2_top = [m.symbol for m in top_metrics if m.symbol not in core]
    
    # Take top tier2 to fill remaining slots
    tier2_slots = max(0, max_active - len(core))
    rotated = tier2_top[:tier2_slots]
    
    # TODO: Persist to configs/universe.yaml
    # For now, just return the rotation plan
    
    return {
        "ok": True,
        "rotated": rotated,
        "core": core,
        "total_active": len(core) + len(rotated),
        "message": "Universe rotation computed (not persisted yet)"
    }



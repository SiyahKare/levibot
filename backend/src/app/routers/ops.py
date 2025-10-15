"""Ops router - operational tools and replay status."""

from __future__ import annotations

from fastapi import APIRouter

from ...ops.replay import get_replay

router = APIRouter(prefix="/ops", tags=["ops"])


@router.get("/replay/status")
async def replay_status():
    """
    Get current replay status.

    Returns:
        Status dictionary with:
        - running: whether replay is active
        - symbol: current symbol being replayed
        - window: replay window type
        - progress_pct: progress percentage (0-100)
        - bars_done/bars_total: progress counters
        - started_at: replay start timestamp
        - current_ts: current bar timestamp
    """
    s = get_replay().get_status()

    return {
        "running": s.running,
        "symbol": s.symbol,
        "window": s.window,
        "progress_pct": round(s.progress_pct, 2),
        "bars_done": s.bars_done,
        "bars_total": s.bars_total,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "current_ts": s.current_ts.isoformat() if s.current_ts else None,
    }


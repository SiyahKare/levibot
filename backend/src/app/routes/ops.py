"""
Ops Router
Operational endpoints for monitoring, replay status, health checks
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, Request

from ...infra.audit import audit
from ...infra.security import require_admin

router = APIRouter(prefix="/ops", tags=["ops"])

# In-memory signal log (last 100 signals)
_SIGNAL_LOG: list[dict[str, Any]] = []


@router.get("/replay/status")
def replay_status() -> dict[str, Any]:
    """
    Get status of last nightly replay job.

    Returns:
        Replay job status and results
    """
    # Check for replay report file
    report_path = os.getenv(
        "REPLAY_REPORT_PATH", "backend/data/reports/replay_latest.json"
    )

    # Try to find latest report
    reports_dir = Path("backend/data/reports")
    if reports_dir.exists():
        replay_files = sorted(reports_dir.glob("replay_*.json"), reverse=True)
        if replay_files:
            report_path = str(replay_files[0])

    if not os.path.exists(report_path):
        return {
            "ok": False,
            "status": "no_report",
            "message": "No replay report found",
            "last_check": datetime.utcnow().isoformat(),
        }

    try:
        with open(report_path) as f:
            data = json.load(f)

        return {
            "ok": True,
            "status": (
                "success"
                if data.get("drift_detection", {}).get("tolerance_ok", False)
                else "drift_detected"
            ),
            "data": data,
            "timestamp": data.get("timestamp", datetime.utcnow().isoformat()),
            "file": report_path,
        }

    except Exception as e:
        return {"ok": False, "status": "error", "error": str(e), "file": report_path}


@router.get("/health")
def ops_health() -> dict[str, Any]:
    """
    Operational health check.

    Returns:
        System operational status
    """
    return {
        "ok": True,
        "service": "ops",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "api": "healthy",
            "database": "unknown",  # Would check actual DB connection
            "redis": "unknown",  # Would check actual Redis connection
            "disk_space": "ok",
        },
    }


@router.get("/version")
def get_version() -> dict[str, Any]:
    """
    Get API version and build info.

    Returns:
        Version information
    """
    return {
        "ok": True,
        "version": "1.7.0",
        "build_date": "2025-10-10",
        "features": [
            "LLM Trade Reason",
            "Confidence Deciles",
            "Strategy Toggles",
            "Risk Presets",
            "AI Predict Stub",
            "Replay Badge",
            "Config Snapshot",
        ],
    }


@router.post("/snapshot")
def snapshot_flags(
    req: Request = None, _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Take a snapshot of current runtime flags.

    Returns:
        Snapshot metadata including file path

    Requires admin authentication.
    """
    from ..routes.admin import get_flags

    # Get current flags (response includes {ok, flags})
    flags_response = get_flags()
    flags = flags_response.get("flags", {})

    # Prepare snapshot directory
    snap_dir = os.getenv("SNAP_DIR", "ops/config-snapshots")
    os.makedirs(snap_dir, exist_ok=True)

    # Create snapshot file
    timestamp = int(time.time())
    snapshot_data = {
        "timestamp": timestamp,
        "datetime": datetime.utcnow().isoformat(),
        "flags": flags,
    }

    file_path = os.path.join(snap_dir, f"flags_{timestamp}.json")

    with open(file_path, "w") as f:
        json.dump(snapshot_data, f, indent=2)

    # Audit log
    audit(
        "snapshot",
        {"path": file_path, "ip": req.client.host if req and req.client else "unknown"},
    )

    return {
        "ok": True,
        "path": file_path,
        "timestamp": timestamp,
        "message": f"Snapshot saved to {file_path}",
    }


@router.post("/signal_log")
def push_signal(
    symbol: str = Body(...),
    side: str = Body(...),
    confidence: float = Body(...),
    strategy: str = Body("telegram_llm"),
    source: str = Body("telegram"),
) -> dict[str, Any]:
    """
    Log a trading signal.

    Args:
        symbol: Trading pair
        side: buy | sell
        confidence: Signal confidence (0.0-1.0)
        strategy: Strategy name (default: telegram_llm)
        source: Signal source (default: telegram)

    Returns:
        Success status
    """
    global _SIGNAL_LOG

    signal = {
        "ts": time.time(),
        "symbol": symbol,
        "side": side,
        "confidence": confidence,
        "strategy": strategy,
        "source": source,
    }

    # Add to front of list
    _SIGNAL_LOG.insert(0, signal)

    # Keep only last 100
    del _SIGNAL_LOG[100:]

    return {
        "ok": True,
        "signal": signal,
        "total": len(_SIGNAL_LOG),
    }


@router.get("/signal_log")
def list_signals(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    """
    Get recent trading signals.

    Args:
        limit: Max number of signals to return (default: 20, max: 100)

    Returns:
        List of recent signals
    """
    return {
        "ok": True,
        "items": _SIGNAL_LOG[:limit],
        "total": len(_SIGNAL_LOG),
    }

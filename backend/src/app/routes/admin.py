"""
Admin Control Endpoints
Canary mode, kill switch, ve prod rollout kontrolü için admin endpoint'leri
"""
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from ...infra.audit import audit
from ...infra.flags_store import load_flags as load_flags_store
from ...infra.flags_store import merge_flags
from ...infra.flags_store import save_flags as save_flags_store
from ...infra.security import require_admin
from ...infra.settings import settings

# Telegram alerts
try:
    from ...infra.telegram_alerts import (
        alert_kill_switch_activated,
        alert_kill_switch_deactivated,
    )
except ImportError:
    def alert_kill_switch_activated(*args, **kwargs): pass
    def alert_kill_switch_deactivated(*args, **kwargs): pass

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/flags")
def get_flags() -> dict[str, Any]:
    """
    Get current runtime flags (merged from file + runtime settings).
    """
    flags = load_flags_store()
    
    # Add runtime values (overwriting file values with current runtime state)
    flags.update({
        "canary_mode": getattr(settings, "CANARY", False),
        "killed": getattr(settings, "KILLED", False),
        "max_daily_loss": settings.MAX_DAILY_LOSS,
        "max_pos_notional": settings.MAX_POS_NOTIONAL,
        "slippage_bps": settings.SLIPPAGE_BPS,
        "allow_symbols": settings.SYMBOLS,
    })
    
    # Add strategies (current runtime state)
    try:
        from .strategy import STRATEGIES
        flags["strategies"] = dict(STRATEGIES)
    except Exception:
        pass
    
    return {"ok": True, "flags": flags}


@router.post("/flags")
def set_flags(
    payload: dict = Body(...),
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Update runtime flags and persist to storage.
    
    Args:
        payload: Dictionary of flags to update
    
    Requires admin authentication.
    """
    from ..main import apply_flags
    
    # Apply to runtime
    apply_flags(payload)
    
    # Persist to file
    save_flags_store(payload)
    
    # Audit log
    audit("flags_update", {
        "ip": req.client.host if req and req.client else "unknown",
        "keys": list(payload.keys())
    })
    
    return {
        "ok": True,
        "saved": payload,
        "message": "Flags updated and persisted"
    }


@router.post("/canary/{state}")
def set_canary(
    state: str,
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Enable/disable canary mode.
    
    Canary mode restricts trading to allow_symbols only.
    
    Args:
        state: "on" or "off"
    
    Requires admin authentication.
    """
    state_lower = state.lower()
    if state_lower not in ("on", "off"):
        raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")
    
    canary_enabled = (state_lower == "on")
    
    # Update runtime
    settings.CANARY = canary_enabled
    
    # Persist
    merge_flags({"canary_mode": canary_enabled})
    
    # Audit log
    audit("canary", {
        "state": state_lower,
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    return {
        "ok": True,
        "canary_mode": canary_enabled,
        "allow_symbols": settings.SYMBOLS,
    }


@router.post("/kill")
def emergency_kill(
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Emergency kill switch - stops all trading immediately.
    
    This sets the global 'killed' flag which trading engines check
    before submitting any orders.
    
    Requires admin authentication.
    """
    # Update runtime
    settings.KILLED = True
    
    # Persist
    merge_flags({"killed": True})
    
    # Audit log
    audit("kill", {
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    # Telegram alert
    alert_kill_switch_activated(reason="manual")
    
    return {
        "ok": True,
        "killed": True,
        "message": "Emergency kill switch activated. All trading stopped.",
    }


@router.post("/unkill")
def reset_kill(
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Reset the kill switch to resume trading.
    
    Requires admin authentication.
    """
    # Update runtime
    settings.KILLED = False
    
    # Persist
    merge_flags({"killed": False})
    
    # Audit log
    audit("unkill", {
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    # Telegram alert
    alert_kill_switch_deactivated()
    
    return {
        "ok": True,
        "killed": False,
        "message": "Kill switch deactivated. Trading can resume.",
    }


@router.post("/set-flag")
def set_flag(
    key: str,
    value: Any,
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Set a runtime flag dynamically.
    
    Args:
        key: Flag name
        value: Flag value (any type)
    
    Requires admin authentication.
    """
    # Merge single flag update
    merge_flags({key: value})
    
    # Audit log
    audit("set_flag", {
        "key": key,
        "value": str(value),
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    return {
        "ok": True,
        "key": key,
        "value": value,
    }


@router.get("/health")
def admin_health() -> dict[str, Any]:
    """Admin health check."""
    return {
        "ok": True,
        "canary_mode": getattr(settings, "CANARY", False),
        "killed": getattr(settings, "KILLED", False),
        "allow_symbols": settings.SYMBOLS,
    }


def is_killed() -> bool:
    """Check if kill switch is active."""
    return getattr(settings, "KILLED", False)


def is_canary_mode() -> bool:
    """Check if canary mode is active."""
    return getattr(settings, "CANARY", False)


def get_allow_symbols() -> list[str]:
    """Get list of allowed symbols in canary mode."""
    return settings.SYMBOLS


def check_daily_loss(current_pnl: float) -> bool:
    """
    Check if daily loss exceeds limit.
    
    Args:
        current_pnl: Current daily PnL in USD
    
    Returns:
        True if within limit, False if exceeded
    """
    return current_pnl > settings.MAX_DAILY_LOSS


@router.post("/ai_reason/{state}")
def ai_reason_toggle(
    state: str,
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Enable/disable AI trade reasons.
    
    Args:
        state: "on" or "off"
    
    Returns:
        Current AI reason status
    
    Requires admin authentication.
    """
    state_lower = state.lower()
    if state_lower not in ("on", "off"):
        raise HTTPException(status_code=400, detail="State must be 'on' or 'off'")
    
    settings.AI_REASON_ENABLED = (state_lower == "on")
    
    # Audit log
    audit("ai_reason_toggle", {
        "state": state_lower,
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    return {
        "ok": True,
        "AI_REASON_ENABLED": settings.AI_REASON_ENABLED,
        "message": f"AI reasons {'enabled' if settings.AI_REASON_ENABLED else 'disabled'}"
    }


@router.get("/ai_reason/status")
def ai_reason_status() -> dict[str, Any]:
    """
    Get AI reason configuration and usage stats.
    
    Returns:
        AI reason status including:
        - enabled: Whether AI reasons are enabled
        - timeout_s: Timeout for AI calls
        - monthly_budget: Monthly token budget
        - used_this_month: Tokens used this month
    """
    from ...ai.openai_client import _ai_tokens_month
    
    return {
        "ok": True,
        "enabled": settings.AI_REASON_ENABLED,
        "timeout_s": settings.AI_REASON_TIMEOUT_S,
        "monthly_budget": settings.AI_REASON_MONTHLY_TOKEN_BUDGET,
        "used_this_month": _ai_tokens_month["used"],
        "month": _ai_tokens_month["month"],
    }


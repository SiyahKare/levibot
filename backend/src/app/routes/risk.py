"""
Risk Router
Risk management presets and dynamic risk parameter control
"""
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ...infra.audit import audit
from ...infra.flags_store import merge_flags
from ...infra.security import require_admin
from ...infra.settings import settings

# Telegram alerts
try:
    from ...infra.telegram_alerts import (
        alert_cooldown_cleared,
        alert_cooldown_triggered,
        alert_guardrails_rejection,
    )
except ImportError:
    # Fallback if telegram_alerts not available
    def alert_cooldown_triggered(*args, **kwargs): pass
    def alert_cooldown_cleared(*args, **kwargs): pass
    def alert_guardrails_rejection(*args, **kwargs): pass

router = APIRouter(prefix="/risk", tags=["risk"])

# Risk presets
PRESETS = {
    "safe": {
        "MAX_DAILY_LOSS": -100.0,
        "MAX_POS_NOTIONAL": 500.0,
        "SLIPPAGE_BPS": 3.0,
        "MAX_LEVERAGE": 2.0,
        "MAX_OPEN_POSITIONS": 3
    },
    "normal": {
        "MAX_DAILY_LOSS": -200.0,
        "MAX_POS_NOTIONAL": 2000.0,
        "SLIPPAGE_BPS": 2.0,
        "MAX_LEVERAGE": 3.0,
        "MAX_OPEN_POSITIONS": 5
    },
    "aggressive": {
        "MAX_DAILY_LOSS": -400.0,
        "MAX_POS_NOTIONAL": 5000.0,
        "SLIPPAGE_BPS": 1.5,
        "MAX_LEVERAGE": 5.0,
        "MAX_OPEN_POSITIONS": 10
    },
}

_CURRENT_PRESET = "normal"

# Guardrails State
class GuardrailsConfig(BaseModel):
    confidence_threshold: float = 0.55
    max_trade_usd: float = 500.0
    max_daily_loss: float = -200.0
    cooldown_minutes: int = 30
    circuit_breaker_latency_ms: int = 300
    circuit_breaker_enabled: bool = True
    symbol_allowlist: list[str] = ["BTCUSDT", "ETHUSDT"]

_GUARDRAILS = GuardrailsConfig()
_COOLDOWN_UNTIL: datetime | None = None


@router.get("/presets")
def list_presets() -> dict[str, Any]:
    """
    List all available risk presets.
    
    Returns:
        Available risk presets with their parameters
    """
    return {
        "ok": True,
        "presets": PRESETS,
        "current": _CURRENT_PRESET
    }


@router.post("/preset/{name}")
def set_preset(
    name: str,
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Apply a risk preset.
    
    Args:
        name: Preset name (safe, normal, aggressive)
    
    Returns:
        Applied preset parameters
    
    Requires admin authentication.
    """
    global _CURRENT_PRESET
    
    preset = PRESETS.get(name)
    if not preset:
        raise HTTPException(
            status_code=404,
            detail=f"Preset '{name}' not found. Available: {list(PRESETS.keys())}"
        )
    
    # Apply preset to settings
    settings.MAX_DAILY_LOSS = preset["MAX_DAILY_LOSS"]
    settings.MAX_POS_NOTIONAL = preset["MAX_POS_NOTIONAL"]
    settings.SLIPPAGE_BPS = preset["SLIPPAGE_BPS"]
    
    _CURRENT_PRESET = name
    
    # Persist to flags
    merge_flags({
        "max_daily_loss": preset["MAX_DAILY_LOSS"],
        "max_pos_notional": preset["MAX_POS_NOTIONAL"],
        "slippage_bps": preset["SLIPPAGE_BPS"],
        "risk_preset": name,
    })
    
    # Audit log
    audit("risk_preset", {
        "name": name,
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    return {
        "ok": True,
        "preset": name,
        "applied": preset,
        "message": f"Risk preset '{name}' applied successfully"
    }


@router.get("/current")
def get_current_risk() -> dict[str, Any]:
    """
    Get current risk parameters.
    
    Returns:
        Current risk settings
    """
    return {
        "ok": True,
        "preset": _CURRENT_PRESET,
        "parameters": {
            "MAX_DAILY_LOSS": settings.MAX_DAILY_LOSS,
            "MAX_POS_NOTIONAL": settings.MAX_POS_NOTIONAL,
            "SLIPPAGE_BPS": settings.SLIPPAGE_BPS,
            "FEE_TAKER_BPS": settings.FEE_TAKER_BPS,
            "FEE_MAKER_BPS": settings.FEE_MAKER_BPS,
        }
    }


@router.post("/parameter")
def update_parameter(name: str, value: float) -> dict[str, Any]:
    """
    Update a single risk parameter.
    
    Args:
        name: Parameter name
        value: New value
    
    Returns:
        Updated parameter
    """
    allowed_params = {
        "MAX_DAILY_LOSS": "MAX_DAILY_LOSS",
        "MAX_POS_NOTIONAL": "MAX_POS_NOTIONAL",
        "SLIPPAGE_BPS": "SLIPPAGE_BPS"
    }
    
    if name not in allowed_params:
        raise HTTPException(
            status_code=400,
            detail=f"Parameter '{name}' not allowed. Available: {list(allowed_params.keys())}"
        )
    
    setattr(settings, allowed_params[name], value)
    
    return {
        "ok": True,
        "parameter": name,
        "value": value,
        "message": f"Parameter '{name}' updated to {value}"
    }


# ========== GUARDRAILS ENDPOINTS ==========

@router.get("/guardrails")
def get_guardrails() -> dict[str, Any]:
    """
    Get current trade guardrails configuration.
    
    Returns:
        Current guardrails settings including confidence threshold,
        trade caps, cooldown, circuit breaker, and symbol allowlist
    """
    global _COOLDOWN_UNTIL
    
    cooldown_active = False
    cooldown_remaining_sec = 0
    
    if _COOLDOWN_UNTIL:
        now = datetime.utcnow()
        if now < _COOLDOWN_UNTIL:
            cooldown_active = True
            cooldown_remaining_sec = int((_COOLDOWN_UNTIL - now).total_seconds())
        else:
            _COOLDOWN_UNTIL = None
    
    return {
        "ok": True,
        "guardrails": {
            "confidence_threshold": _GUARDRAILS.confidence_threshold,
            "max_trade_usd": _GUARDRAILS.max_trade_usd,
            "max_daily_loss": _GUARDRAILS.max_daily_loss,
            "cooldown_minutes": _GUARDRAILS.cooldown_minutes,
            "circuit_breaker_latency_ms": _GUARDRAILS.circuit_breaker_latency_ms,
            "circuit_breaker_enabled": _GUARDRAILS.circuit_breaker_enabled,
            "symbol_allowlist": _GUARDRAILS.symbol_allowlist,
        },
        "state": {
            "cooldown_active": cooldown_active,
            "cooldown_remaining_sec": cooldown_remaining_sec,
        }
    }


@router.post("/guardrails")
def update_guardrails(
    payload: dict[str, Any],
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Update trade guardrails configuration.
    
    Args:
        payload: New guardrails settings (partial updates allowed)
    
    Returns:
        Updated guardrails
    
    Requires admin authentication.
    """
    global _GUARDRAILS
    
    # Update fields if provided
    if "confidence_threshold" in payload:
        val = float(payload["confidence_threshold"])
        if not 0.0 <= val <= 1.0:
            raise HTTPException(status_code=400, detail="confidence_threshold must be between 0 and 1")
        _GUARDRAILS.confidence_threshold = val
    
    if "max_trade_usd" in payload:
        val = float(payload["max_trade_usd"])
        if val <= 0:
            raise HTTPException(status_code=400, detail="max_trade_usd must be positive")
        _GUARDRAILS.max_trade_usd = val
    
    if "max_daily_loss" in payload:
        _GUARDRAILS.max_daily_loss = float(payload["max_daily_loss"])
    
    if "cooldown_minutes" in payload:
        val = int(payload["cooldown_minutes"])
        if val < 0:
            raise HTTPException(status_code=400, detail="cooldown_minutes must be non-negative")
        _GUARDRAILS.cooldown_minutes = val
    
    if "circuit_breaker_latency_ms" in payload:
        val = int(payload["circuit_breaker_latency_ms"])
        if val < 0:
            raise HTTPException(status_code=400, detail="circuit_breaker_latency_ms must be non-negative")
        _GUARDRAILS.circuit_breaker_latency_ms = val
    
    if "circuit_breaker_enabled" in payload:
        _GUARDRAILS.circuit_breaker_enabled = bool(payload["circuit_breaker_enabled"])
    
    if "symbol_allowlist" in payload:
        allowlist = payload["symbol_allowlist"]
        if not isinstance(allowlist, list):
            raise HTTPException(status_code=400, detail="symbol_allowlist must be a list")
        _GUARDRAILS.symbol_allowlist = allowlist
    
    # Persist to flags
    merge_flags({
        "guardrails_confidence_threshold": _GUARDRAILS.confidence_threshold,
        "guardrails_max_trade_usd": _GUARDRAILS.max_trade_usd,
        "guardrails_max_daily_loss": _GUARDRAILS.max_daily_loss,
        "guardrails_cooldown_minutes": _GUARDRAILS.cooldown_minutes,
        "guardrails_circuit_breaker_latency_ms": _GUARDRAILS.circuit_breaker_latency_ms,
        "guardrails_circuit_breaker_enabled": _GUARDRAILS.circuit_breaker_enabled,
        "guardrails_symbol_allowlist": _GUARDRAILS.symbol_allowlist,
    })
    
    # Audit log
    audit("guardrails_update", {
        "changes": payload,
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    return {
        "ok": True,
        "guardrails": _GUARDRAILS.dict(),
        "message": "Guardrails updated successfully"
    }


@router.post("/guardrails/trigger-cooldown")
def trigger_cooldown(
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Manually trigger trading cooldown.
    
    Returns:
        Cooldown status
    
    Requires admin authentication.
    """
    global _COOLDOWN_UNTIL
    
    _COOLDOWN_UNTIL = datetime.utcnow() + timedelta(minutes=_GUARDRAILS.cooldown_minutes)
    
    # Audit log
    audit("cooldown_trigger", {
        "cooldown_until": _COOLDOWN_UNTIL.isoformat(),
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    # Telegram alert
    alert_cooldown_triggered(_GUARDRAILS.cooldown_minutes, reason="manual")
    
    return {
        "ok": True,
        "cooldown_active": True,
        "cooldown_until": _COOLDOWN_UNTIL.isoformat(),
        "message": f"Cooldown triggered for {_GUARDRAILS.cooldown_minutes} minutes"
    }


@router.post("/guardrails/clear-cooldown")
def clear_cooldown(
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Clear active trading cooldown.
    
    Returns:
        Cooldown status
    
    Requires admin authentication.
    """
    global _COOLDOWN_UNTIL
    
    _COOLDOWN_UNTIL = None
    
    # Audit log
    audit("cooldown_clear", {
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    # Telegram alert
    alert_cooldown_cleared()
    
    return {
        "ok": True,
        "cooldown_active": False,
        "message": "Cooldown cleared"
    }


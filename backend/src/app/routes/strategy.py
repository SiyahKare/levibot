"""
Strategy Router
Enable/disable trading strategies and view per-strategy performance
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ...infra.audit import audit
from ...infra.flags_store import load_flags, merge_flags
from ...infra.security import require_admin

router = APIRouter(prefix="/strategy", tags=["strategy"])

# In-memory strategy toggles (persisted via flags.yaml in production)
STRATEGIES = {
    "telegram_llm": True,
    "mean_revert": False,
    "momentum": False,
    "arbitrage": False,
}


@router.get("/")
def list_strategies() -> list[dict[str, Any]]:
    """
    List all available strategies with their ON/OFF status.
    
    Returns:
        List of strategies with name and enabled status
    """
    return [
        {"name": name, "enabled": enabled, "description": _get_description(name)}
        for name, enabled in STRATEGIES.items()
    ]


@router.post("/{name}/toggle")
def toggle_strategy(
    name: str,
    enabled: bool,
    req: Request = None,
    _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Enable or disable a specific strategy.
    
    Args:
        name: Strategy name
        enabled: True to enable, False to disable
    
    Returns:
        Updated strategy status
    
    Requires admin authentication.
    """
    if name not in STRATEGIES:
        raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")
    
    # Update in-memory
    STRATEGIES[name] = enabled
    
    # Persist to flags
    flags = load_flags()
    strategies_dict = flags.get("strategies", {})
    strategies_dict[name] = enabled
    merge_flags({"strategies": strategies_dict})
    
    # Audit log
    audit("strategy_toggle", {
        "name": name,
        "enabled": enabled,
        "ip": req.client.host if req and req.client else "unknown"
    })
    
    return {
        "ok": True,
        "name": name,
        "enabled": STRATEGIES[name],
        "message": f"Strategy '{name}' {'enabled' if enabled else 'disabled'}"
    }


@router.get("/{name}/status")
def strategy_status(name: str) -> dict[str, Any]:
    """
    Get status of a specific strategy.
    
    Args:
        name: Strategy name
    
    Returns:
        Strategy status and stats
    """
    if name not in STRATEGIES:
        raise HTTPException(status_code=404, detail=f"Strategy '{name}' not found")
    
    return {
        "ok": True,
        "name": name,
        "enabled": STRATEGIES[name],
        "description": _get_description(name),
        "stats": {
            "total_signals": 0,
            "active_trades": 0,
            "pnl_24h": 0.0
        }
    }


def _get_description(name: str) -> str:
    """Get strategy description."""
    descriptions = {
        "telegram_llm": "AI-powered Telegram signal trading",
        "mean_revert": "Mean reversion strategy",
        "momentum": "Momentum-based trading",
        "arbitrage": "Cross-exchange arbitrage"
    }
    return descriptions.get(name, "No description available")


def is_strategy_enabled(name: str) -> bool:
    """
    Check if a strategy is enabled.
    
    Args:
        name: Strategy name
    
    Returns:
        True if enabled, False otherwise
    """
    return STRATEGIES.get(name, False)


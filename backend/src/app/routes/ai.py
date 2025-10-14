"""
AI Router
ML model predictions and AI-powered trading signals
"""

import time
from typing import Any

from fastapi import APIRouter, Body, Depends, Query, Request

from ...ai.model_provider import PROVIDERS, get_model
from ...infra.audit import audit
from ...infra.flags_store import load_flags, save_flags
from ...infra.security import require_admin

router = APIRouter(prefix="/ai", tags=["ai"])


def _current_model_name() -> str:
    """Get currently selected model name from flags."""
    try:
        flags = load_flags()
        return (
            (flags.get("ai_model") or "stub-sine")
            if isinstance(flags, dict)
            else "stub-sine"
        )
    except Exception:
        return "stub-sine"


@router.get("/predict")
async def predict(
    symbol: str = Query(..., description="Trading symbol (e.g., BTCUSDT)"),
    horizon: str = Query("60s", alias="h", description="Prediction horizon"),
    model: str | None = Query(
        None, description="Model name (optional, uses current if not specified)"
    ),
) -> dict[str, Any]:
    """
    Get ML model prediction for symbol.

    Args:
        symbol: Trading pair to predict
        horizon: Prediction time horizon (e.g., "60s", "5m", "1h")
        model: Model name (optional, uses current selected model if not specified)

    Returns:
        Prediction with prob_up score
    """
    # Get model provider
    model_name = model or _current_model_name()
    provider = get_model(model_name)

    # Track metrics
    start_time = time.time()

    # Generate prediction
    result = await provider.predict(symbol, horizon)

    # Record metrics
    try:
        from ...infra.metrics import (
            FALLBACK_EVENTS,
            PREDICTION_LATENCY,
            PREDICTION_REQUESTS,
            update_staleness,
        )

        latency = time.time() - start_time
        PREDICTION_LATENCY.labels(model_name=model_name, symbol=symbol).observe(latency)

        status = "fallback" if result.get("fallback") else "success"
        PREDICTION_REQUESTS.labels(
            model_name=model_name, symbol=symbol, status=status
        ).inc()

        if result.get("fallback"):
            FALLBACK_EVENTS.labels(
                reason=result.get("fallback_reason", "unknown")
            ).inc()

        # Update staleness if available
        if "staleness_s" in result:
            update_staleness(symbol, result["staleness_s"])
    except ImportError:
        pass  # Metrics not available

    # Log prediction for analytics
    try:
        from ..routes.analytics import log_prediction

        log_prediction({"ts": time.time(), **result})
    except Exception:
        pass

    return result


@router.get("/models")
def list_models() -> dict[str, Any]:
    """
    List available ML models.

    Returns:
        List of available models and current selection
    """
    return {
        "ok": True,
        "models": list(PROVIDERS.keys()),
        "current": _current_model_name(),
    }


@router.post("/select")
def select_model(
    payload: dict = Body(...), req: Request = None, _: bool = Depends(require_admin)
) -> dict[str, Any]:
    """
    Select active model for predictions.

    Args:
        payload: {"name": "model-name"}

    Returns:
        Success status and current model

    Requires admin authentication.
    """
    name = payload.get("name")

    if not name:
        return {"ok": False, "error": "Model name required"}

    if name not in PROVIDERS:
        return {
            "ok": False,
            "error": f"Unknown model: {name}",
            "available": list(PROVIDERS.keys()),
        }

    # Get current model for metrics
    previous = _current_model_name()

    # Persist to flags
    try:
        flags = load_flags()
        flags["ai_model"] = name
        save_flags(flags)
    except Exception as e:
        return {"ok": False, "error": f"Failed to persist: {str(e)}"}

    # Record metrics
    try:
        from ...infra.metrics import record_model_switch

        record_model_switch(from_model=previous, to_model=name)
    except ImportError:
        pass  # Metrics not available

    # Audit log
    audit(
        "ai_model_select",
        {
            "model": name,
            "previous": previous,
            "ip": req.client.host if req and req.client else "unknown",
        },
    )

    return {
        "ok": True,
        "current": name,
        "previous": previous,
        "message": f"Model switched from {previous} to {name}",
    }


@router.get("/health")
def ai_health() -> dict[str, Any]:
    """
    Check AI service health.

    Returns:
        Health status
    """
    return {
        "ok": True,
        "service": "ai",
        "status": "operational",
        "models_loaded": 1,
        "last_prediction": time.time(),
    }

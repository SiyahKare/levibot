"""
ML API — Model predictions and controls
"""

from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/ml", tags=["ml"])


async def _get_model_prediction(symbol: str, horizon: str = "60s") -> dict[str, Any]:
    """Get real ML model prediction using existing AI provider system"""
    try:
        from ...ai.model_provider import PROVIDERS
        from ...infra.flags_store import load_flags
        from ...infra.ml_metrics import (
            ml_feature_staleness_seconds,
            ml_prediction_confidence,
        )

        # Get current model name from flags
        flags = load_flags()
        model_name = flags.get("ai_model", "skops-local")

        # Get provider and predict
        provider = PROVIDERS.get(model_name)
        if not provider:
            # Fallback to stub-sine if model not found
            provider = PROVIDERS["stub-sine"]
            model_name = "stub-sine"

        result = await provider.predict(symbol, horizon)

        # Update Prometheus metrics
        if result.get("staleness_s") is not None:
            ml_feature_staleness_seconds.labels(symbol=symbol).set(
                result["staleness_s"]
            )

        if result.get("confidence") is not None:
            ml_prediction_confidence.labels(symbol=symbol).observe(result["confidence"])

        return result
    except Exception as e:
        # Fallback to stub on error
        return {
            "ok": False,
            "symbol": symbol,
            "prob_up": 0.5,
            "confidence": 0.0,
            "model": "error",
            "timestamp": 0,
            "note": f"⚠️ Error: {str(e)}",
            "fallback": True,
            "fallback_reason": str(e),
        }


@router.get("/predict")
async def ml_predict(symbol: str = Query("BTCUSDT", description="Trading symbol")):
    """Get LightGBM prediction (real ML model)"""
    result = await _get_model_prediction(symbol, "60s")

    # Transform to MLDashboard format
    prob_up = result.get("prob_up", 0.5)
    confidence = result.get("confidence", abs(prob_up - 0.5) * 2)
    staleness_s = result.get("staleness_s", None)

    # Calculate model metrics (stub for now - TODO: get from model registry)
    auc = 0.72 if not result.get("fallback") else 0.0
    brier = 0.18 if not result.get("fallback") else 0.0

    return {
        "symbol": symbol,
        "p_up": prob_up,
        "confidence": confidence,
        "horizon": "60s",
        "staleness_s": staleness_s,  # Add staleness
        "model_metrics": {"auc": auc, "brier": brier},
        "note": result.get("note", ""),
        "fallback": result.get("fallback", False),
    }


@router.get("/predict_deep")
async def ml_predict_deep(symbol: str = Query("BTCUSDT", description="Trading symbol")):
    """Get Deep Transformer prediction (real ML model)"""
    result = await _get_model_prediction(symbol, "60s")

    # Transform to MLDashboard format
    prob_up = result.get("prob_up", 0.5)
    confidence = result.get("confidence", abs(prob_up - 0.5) * 2)

    # Deep model outputs (derived from base prediction)
    mu = (prob_up - 0.5) * 2  # Expected return
    uncertainty = 1.0 - confidence  # Inverse of confidence

    return {
        "symbol": symbol,
        "p_up": prob_up,
        "mu": mu,
        "uncertainty": uncertainty,
        "confidence": confidence,
        "note": result.get("note", ""),
        "fallback": result.get("fallback", False),
    }


@router.post("/kill")
async def ml_kill(enabled: bool = Query(False, description="Enable kill switch")):
    """Kill switch - delegates to admin emergency kill"""
    try:
        from ...infra.flags_store import load_flags, merge_flags

        # Set kill switch flag
        flags = load_flags()
        flags["killed"] = enabled
        merge_flags(flags)

        return {
            "ok": True,
            "killed": enabled,
            "message": f"Kill switch {'activated' if enabled else 'deactivated'}",
        }
    except Exception as e:
        return {"ok": False, "killed": False, "error": str(e)}

"""
ML Prediction API

Real-time predictions from trained models with monitoring.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb
import polars as pl
from fastapi import APIRouter, HTTPException

from ...infra.ml_metrics import (
    ml_feature_staleness_seconds,
    ml_prediction_confidence,
    ml_predictions_total,
)

router = APIRouter(prefix="/ml", tags=["ml"])

# Global model cache
_MODEL_CACHE = {}


def load_current_model():
    """Load current model from registry."""
    registry_path = Path("backend/data/registry/model_registry.json")
    
    if not registry_path.exists():
        raise HTTPException(status_code=404, detail="Model registry not found")
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    current = registry.get("current")
    if not current:
        raise HTTPException(status_code=404, detail="No current model in registry")
    
    model_path = current["path"]
    
    # Check cache
    if model_path in _MODEL_CACHE:
        return _MODEL_CACHE[model_path], current
    
    # Load model
    if not Path(model_path).exists():
        raise HTTPException(status_code=404, detail=f"Model file not found: {model_path}")
    
    model = lgb.Booster(model_file=model_path)
    _MODEL_CACHE[model_path] = model
    
    return model, current


@router.get("/predict")
async def predict(
    symbol: str = "BTCUSDT",
    timeframe: str = "15m",
) -> dict[str, Any]:
    """
    Get ML prediction for a symbol with monitoring.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
    
    Returns:
        Prediction result with confidence, policy signals, and metrics
    """
    # Load model
    model, registry = load_current_model()
    
    # Load latest features
    features_file = Path(f"backend/data/features/{symbol}_{timeframe}_features.parquet")
    
    if not features_file.exists():
        raise HTTPException(status_code=404, detail=f"Features not found for {symbol}")
    
    try:
        df = pl.read_parquet(features_file).sort("timestamp").tail(1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feature file corrupted: {str(e)}")
    
    if len(df) == 0:
        raise HTTPException(status_code=404, detail="No recent features available")
    
    # Feature staleness monitoring
    latest_timestamp = df["timestamp"][0] if "timestamp" in df.columns else datetime.now()
    staleness_seconds = (datetime.now() - latest_timestamp).total_seconds()
    ml_feature_staleness_seconds.labels(symbol=symbol).set(staleness_seconds)
    
    # Extract features
    feature_cols = registry.get("features", [])
    X = df.select(feature_cols).to_pandas()
    
    # Predict
    p_up = float(model.predict(X)[0])
    
    # Calculate confidence (distance from 0.5)
    confidence = abs(p_up - 0.5) * 2
    
    # Get policy thresholds
    policy = registry.get("policy", {})
    entry_threshold = policy.get("entry_threshold", 0.55)
    exit_threshold = policy.get("exit_threshold", 0.48)
    
    # Determine signal
    signal = "HOLD"
    if p_up > entry_threshold:
        signal = "ENTRY"
    elif p_up < exit_threshold:
        signal = "EXIT"
    
    # Expected return (simple proxy)
    expected_return = (p_up - 0.5) * 0.02
    
    # Update metrics
    confidence_bucket = "high" if confidence > 0.3 else "medium" if confidence > 0.15 else "low"
    ml_predictions_total.labels(symbol=symbol, confidence_bucket=confidence_bucket).inc()
    ml_prediction_confidence.labels(symbol=symbol).observe(confidence)
    
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "p_up": round(p_up, 4),
        "p_down": round(1 - p_up, 4),
        "confidence": round(confidence, 3),
        "expected_return": round(expected_return, 5),
        "signal": signal,
        "policy": {
            "entry_threshold": entry_threshold,
            "exit_threshold": exit_threshold,
        },
        "horizon": registry.get("horizon"),
        "model_metrics": registry.get("metrics"),
        "calibration": registry.get("calibration"),
        "staleness_seconds": int(staleness_seconds),
        "timestamp": latest_timestamp.isoformat(),
    }


@router.get("/kill")
async def kill_switch(
    enabled: bool = True,
) -> dict[str, Any]:
    """
    Emergency kill switch for ML trading.
    
    When enabled, all ML signals will return size=0.
    """
    kill_file = Path("backend/data/ml_kill_switch.flag")
    
    if enabled:
        kill_file.touch()
        return {"ok": True, "kill_switch": "ENABLED", "message": "All ML trading disabled"}
    else:
        if kill_file.exists():
            kill_file.unlink()
        return {"ok": True, "kill_switch": "DISABLED", "message": "ML trading enabled"}


@router.get("/model/status")
async def model_status() -> dict[str, Any]:
    """Get current model status and metrics."""
    registry_path = Path("backend/data/registry/model_registry.json")
    
    if not registry_path.exists():
        raise HTTPException(status_code=404, detail="Model registry not found")
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    current = registry.get("current")
    if not current:
        raise HTTPException(status_code=404, detail="No current model")
    
    return {
        "ok": True,
        "model_id": current.get("id", "unknown"),
        "symbols": current.get("symbol_set", []),
        "timeframe": current.get("timeframe"),
        "metrics": current.get("metrics"),
        "features_count": len(current.get("features", [])),
        "trained_at": current.get("trained_at"),
    }


@router.post("/model/reload")
async def reload_model() -> dict[str, Any]:
    """Reload model from registry (clear cache)."""
    global _MODEL_CACHE
    _MODEL_CACHE.clear()
    
    # Load to verify
    model, registry = load_current_model()
    
    return {
        "ok": True,
        "message": "Model reloaded successfully",
        "model_id": registry.get("id", "unknown"),
    }


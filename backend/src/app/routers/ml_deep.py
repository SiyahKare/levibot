"""
Deep Model Prediction API

Inference endpoint for Transformer-based deep models with uncertainty estimation.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl
import torch
from fastapi import APIRouter, HTTPException, Query

from ...infra.ml_metrics import (
    ml_prediction_confidence,
    ml_predictions_total,
    ml_uncertainty,
)

router = APIRouter(prefix="/ml", tags=["ml-deep"])

# Global cache
_DEEP_MODEL_CACHE = {}
_REGISTRY_PATH = Path("backend/data/registry/model_registry.json")


def load_deep_model(symbol: str):
    """Load deep model for a symbol from registry."""
    if not _REGISTRY_PATH.exists():
        raise HTTPException(status_code=404, detail="Model registry not found")

    with open(_REGISTRY_PATH) as f:
        registry = json.load(f)

    deep_registry = registry.get("deep", {})
    if symbol not in deep_registry:
        raise HTTPException(status_code=404, detail=f"No deep model found for {symbol}")

    model_info = deep_registry[symbol]
    model_path = Path(model_info["path"])

    if not model_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Model file not found: {model_path}"
        )

    # Check cache
    cache_key = f"{symbol}_{model_path.stem}"
    if cache_key in _DEEP_MODEL_CACHE:
        return _DEEP_MODEL_CACHE[cache_key], model_info

    # Load model
    from ...ml.models.deep_tfm import SeqTransformer

    checkpoint = torch.load(model_path, map_location="cpu")

    features = checkpoint.get("features") or model_info.get("features")
    model = SeqTransformer(in_dim=len(features))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Cache
    _DEEP_MODEL_CACHE[cache_key] = (model, features, checkpoint.get("seq_len", 128))

    return _DEEP_MODEL_CACHE[cache_key], model_info


@router.get("/predict_deep")
async def predict_deep(
    symbol: str = Query("BTCUSDT", description="Trading symbol"),
    n_samples: int = Query(20, description="MC Dropout samples", ge=5, le=50),
) -> dict[str, Any]:
    """
    Get deep model prediction with uncertainty estimation.

    Uses Monte Carlo Dropout to estimate epistemic uncertainty.

    Returns:
        - p_up: Probability of price going up
        - mu: Expected return
        - uncertainty: Total uncertainty (epistemic + aleatoric)
        - confidence: Model confidence
        - signal: Trading signal (ENTRY/EXIT/HOLD)
    """
    # Load model
    (model, features, seq_len), model_info = load_deep_model(symbol)

    # Load latest features
    data_file = Path("backend/data/feature_multi/fe_multi_15m.parquet")
    if not data_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Multi-asset feature data not found. Run: python backend/ml/feature_store/ingest_multi.py",
        )

    df = pl.read_parquet(data_file).filter(pl.col("symbol") == symbol).sort("timestamp")

    if len(df) < seq_len + 1:
        raise HTTPException(
            status_code=400, detail=f"Not enough data (need {seq_len}+ rows)"
        )

    # Extract features
    X = df.select(features).fill_null(0).to_numpy()[-seq_len:]

    # Prepare input
    x_tensor = torch.tensor(X, dtype=torch.float32).unsqueeze(
        0
    )  # (1, seq_len, n_features)

    # MC Dropout prediction
    from ...ml.models.deep_tfm import mc_predict

    p_up, mu, uncertainty = mc_predict(model, x_tensor, n_samples=n_samples)

    p_up = float(p_up.item())
    mu = float(mu.item())
    uncertainty = float(uncertainty.item())

    # Calculate confidence
    confidence = abs(p_up - 0.5) * 2

    # Determine signal
    signal = "HOLD"
    if p_up > 0.55 and confidence > 0.15:
        signal = "ENTRY"
    elif p_up < 0.45:
        signal = "EXIT"

    # Feature staleness
    latest_timestamp = df["timestamp"][-1]
    staleness_seconds = (datetime.now() - latest_timestamp).total_seconds()

    # Update metrics
    confidence_bucket = (
        "high" if confidence > 0.3 else "medium" if confidence > 0.15 else "low"
    )
    ml_predictions_total.labels(
        symbol=symbol, confidence_bucket=confidence_bucket
    ).inc()
    ml_prediction_confidence.labels(symbol=symbol).observe(confidence)
    ml_uncertainty.labels(symbol=symbol).set(uncertainty)

    return {
        "symbol": symbol,
        "model_type": "deep_transformer",
        "p_up": round(p_up, 4),
        "p_down": round(1 - p_up, 4),
        "mu": round(mu, 6),
        "uncertainty": round(uncertainty, 6),
        "confidence": round(confidence, 3),
        "signal": signal,
        "mc_samples": n_samples,
        "staleness_seconds": int(staleness_seconds),
        "timestamp": latest_timestamp.isoformat(),
        "model_metrics": {
            "val_acc": model_info.get("best_val_acc"),
            "epoch": model_info.get("best_epoch"),
        },
    }


@router.get("/predict_ensemble")
async def predict_ensemble(
    symbol: str = Query("BTCUSDT", description="Trading symbol"),
) -> dict[str, Any]:
    """
    Ensemble prediction combining LightGBM and Deep Transformer.

    Weighted average based on model confidence and historical performance.
    """
    try:
        # Get both predictions
        import httpx

        # LightGBM prediction
        lgbm_response = httpx.get(
            "http://127.0.0.1:8000/ml/predict",
            params={"symbol": symbol},
            timeout=2.0,
        )

        if lgbm_response.status_code != 200:
            lgbm_pred = None
        else:
            lgbm_pred = lgbm_response.json()

        # Deep model prediction
        deep_response = httpx.get(
            "http://127.0.0.1:8000/ml/predict_deep",
            params={"symbol": symbol},
            timeout=3.0,
        )

        if deep_response.status_code != 200:
            deep_pred = None
        else:
            deep_pred = deep_response.json()

        # Ensemble
        if lgbm_pred and deep_pred:
            # Weighted average (favor higher confidence)
            w_lgbm = lgbm_pred["confidence"]
            w_deep = deep_pred["confidence"] * 1.2  # Slight bias to deep model
            w_sum = w_lgbm + w_deep + 1e-9

            p_up = (lgbm_pred["p_up"] * w_lgbm + deep_pred["p_up"] * w_deep) / w_sum
            confidence = (w_lgbm + w_deep) / 2

            signal = "HOLD"
            if p_up > 0.55 and confidence > 0.2:
                signal = "ENTRY"
            elif p_up < 0.45:
                signal = "EXIT"

            return {
                "symbol": symbol,
                "model_type": "ensemble",
                "p_up": round(p_up, 4),
                "confidence": round(confidence, 3),
                "signal": signal,
                "components": {
                    "lgbm": {"p_up": lgbm_pred["p_up"], "weight": round(w_lgbm, 3)},
                    "deep": {"p_up": deep_pred["p_up"], "weight": round(w_deep, 3)},
                },
            }

        elif lgbm_pred:
            return {"symbol": symbol, "model_type": "lgbm_only", **lgbm_pred}

        elif deep_pred:
            return {"symbol": symbol, "model_type": "deep_only", **deep_pred}

        else:
            raise HTTPException(status_code=500, detail="No models available")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ensemble prediction failed: {e}")


@router.get("/models/deep/status")
async def deep_model_status() -> dict[str, Any]:
    """Get status of all deep models."""
    if not _REGISTRY_PATH.exists():
        return {"deep_models": []}

    with open(_REGISTRY_PATH) as f:
        registry = json.load(f)

    deep_registry = registry.get("deep", {})

    models = []
    for symbol, info in deep_registry.items():
        model_path = Path(info["path"])
        models.append(
            {
                "symbol": symbol,
                "path": str(model_path),
                "exists": model_path.exists(),
                "val_acc": info.get("best_val_acc"),
                "features": len(info.get("features", [])),
                "seq_len": info.get("seq_len"),
            }
        )

    return {"deep_models": models, "count": len(models)}

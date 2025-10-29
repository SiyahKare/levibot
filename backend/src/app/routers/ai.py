"""AI router - model cards and real-time predictions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter(tags=["ai"])

MODELS_DIR = Path("backend/data/models")


def _read_model_card(model_dir: Path) -> dict:
    """
    Read model_card.json from directory.

    If not found, create fallback metadata from directory mtime.
    """
    card_path = model_dir / "model_card.json"
    if card_path.exists():
        with open(card_path) as f:
            return json.load(f)

    # Fallback: create metadata from directory
    stat = model_dir.stat()
    return {
        "version": model_dir.name,
        "last_trained": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
        "type": "fallback",
    }


@router.get("/models")
async def ai_models():
    """
    Get metadata for all AI models.

    Returns:
        Model cards for LGBM, TFT, and ensemble configuration
    """
    lgbm_card = None
    tft_card = None

    if MODELS_DIR.exists():
        # Find most recent model directories
        subdirs = sorted([d for d in MODELS_DIR.iterdir() if d.is_dir()], reverse=True)

        for d in subdirs:
            if (d / "lgbm.pkl").exists() and lgbm_card is None:
                card = _read_model_card(d)
                # Add found status
                card["found"] = True
                card["path"] = str(d / "lgbm.pkl")
                lgbm_card = card
            if (d / "tft.pt").exists() and tft_card is None:
                card = _read_model_card(d)
                card["found"] = True
                card["path"] = str(d / "tft.pt")
                tft_card = card
            if lgbm_card and tft_card:
                break

    # Frontend-compatible format
    available_models = ["ensemble"]
    if lgbm_card:
        available_models.append("lgbm")
    if tft_card:
        available_models.append("tft")

    return {
        "ok": True,
        "models": available_models,
        "current": "ensemble",
        "meta": {
            "lgbm": lgbm_card
            or {
                "version": "not_found",
                "status": "Model files not found - upload trained model",
                "found": False,
            },
            "tft": tft_card
            or {
                "version": "not_found",
                "status": "Model files not found - upload trained model",
                "found": False,
            },
            "ensemble": {
                "weights": {"lgbm": 0.5, "tft": 0.3, "sentiment": 0.2},
                "threshold": 0.55,
            },
        },
    }


@router.post("/select")
async def ai_select(body: dict):
    """
    Select active model for predictions.

    Currently, only "ensemble" is supported. This endpoint validates
    the selection and returns success. Future: switch between LGBM/TFT/Ensemble.

    Request body:
        {"name": "ensemble"}

    Returns:
        {"ok": true, "current": "ensemble", "message": "Model selected"}
    """
    model_name = body.get("name", "ensemble")

    # Validate model name
    valid_models = ["ensemble", "lgbm", "tft"]
    if model_name not in valid_models:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {model_name}. Valid: {valid_models}",
        )

    # For now, always use ensemble (model switching can be added later)
    return {
        "ok": True,
        "current": "ensemble",
        "message": f"Model '{model_name}' selected (currently all use ensemble)",
    }


@router.get("/test")
async def ai_test():
    """Simple test endpoint."""
    return {"ok": True, "message": "AI router working"}


@router.get("/simple")
async def ai_simple():
    """Even simpler test endpoint."""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@router.get("/predict")
async def ai_predict(
    symbol: str = Query(
        ..., min_length=3, description="Trading symbol (e.g. BTC/USDT)"
    ),
    timeframe: str = Query("1m", description="Timeframe (1m, 5m, etc.)"),
    horizon: int = Query(5, ge=1, le=60, description="Prediction horizon in minutes"),
):
    """Generate AI prediction for symbol."""
    import random

    # Mock prediction data
    prob_up = random.uniform(0.3, 0.7)
    side = "long" if prob_up > 0.5 else "short"
    confidence = random.uniform(0.6, 0.9)

    # Calculate price target
    base_price = 110000.0 if "BTC" in symbol.upper() else 3000.0
    current_price = base_price
    price_target = current_price * (1 + (prob_up - 0.5) * 0.02)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "horizon": horizon,
        "side": side,
        "prob_up": prob_up,
        "confidence": confidence,
        "price_target": price_target,
        "_current_price": current_price,
        "source": "ensemble",
        "ts": datetime.now(UTC).isoformat(),
        "_prob_lgbm": prob_up * 0.8,
        "_prob_tft": prob_up * 1.2,
        "_prob_sent": prob_up * 0.9,
    }

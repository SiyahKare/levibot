"""AI router - model cards and real-time predictions."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ...adapters.mexc_ccxt import MexcAdapter
from ...data.feature_store import minute_features
from ...ml.infer_lgbm import LGBMProd
from ...ml.models.ensemble_predictor import EnsemblePredictor
from ...ml.tft.infer_tft import TFTProd

router = APIRouter(prefix="/ai", tags=["ai"])

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
            "lgbm": lgbm_card or {
                "version": "not_found",
                "status": "Model files not found - upload trained model",
                "found": False,
            },
            "tft": tft_card or {
                "version": "not_found", 
                "status": "Model files not found - upload trained model",
                "found": False,
            },
            "ensemble": {
                "weights": {"lgbm": 0.5, "tft": 0.3, "sentiment": 0.2},
                "threshold": 0.55,
            },
        }
    }


@router.get("/predict")
async def ai_predict(
    symbol: str = Query(..., min_length=3, description="Trading symbol (e.g. BTC/USDT)"),
    timeframe: str = Query("1m", description="Timeframe (1m, 5m, etc.)"),
    horizon: int = Query(5, ge=1, le=60, description="Prediction horizon in minutes"),
):
    """
    Generate AI prediction for symbol.

    Steps:
    1. Fetch recent OHLCV bars from MEXC
    2. Build features using feature engineering pipeline
    3. Run ensemble prediction (LGBM + TFT + Sentiment)
    4. Log prediction to DuckDB
    5. Return prediction with side/confidence/target

    Args:
        symbol: Trading symbol
        timeframe: Bar timeframe
        horizon: Prediction horizon in minutes

    Returns:
        Prediction dictionary with side, prob_up, confidence, price_target
    """
    # 1) Fetch market data from MEXC
    mexc = MexcAdapter(symbols=[symbol], rate_limit=True)
    try:
        bars = await mexc.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=120)
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Failed to fetch market data: {str(e)}"
        ) from e

    if len(bars) < 60:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough bars for features (got {len(bars)}, need ≥60)",
        )

    # 2) Build features
    import pandas as pd

    df = pd.DataFrame(
        bars, columns=["ts", "open", "high", "low", "close", "volume"]
    )
    try:
        features_df = minute_features(df, horizon=horizon)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Feature engineering failed: {str(e)}"
        ) from e

    if features_df.empty:
        raise HTTPException(status_code=400, detail="Feature engineering produced no data")

    # Get latest feature row
    latest = features_df.iloc[-1].to_dict()

    # 3) Load models and run ensemble prediction
    try:
        lgbm = LGBMProd()
        tft = TFTProd()
        ensemble = EnsemblePredictor(w_lgbm=0.5, w_tft=0.3, w_sent=0.2, threshold=0.55)

        # Run prediction with analytics logging enabled
        prediction = ensemble.predict(
            features=latest,
            sentiment=0.0,  # Default neutral sentiment (TODO: integrate real sentiment)
            symbol=symbol,
            log_to_analytics=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Model inference failed: {str(e)}"
        ) from e

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "horizon": horizon,
        "timestamp": datetime.now(UTC).isoformat(),
        **prediction,
    }


"""
Model Provider Interface
Pluggable ML model providers for real-time predictions
"""

import math
import os
import time
from abc import ABC, abstractmethod
from typing import Any


class BaseModel(ABC):
    """Base class for model providers."""

    name: str

    @abstractmethod
    def predict(self, symbol: str, horizon: str) -> dict[str, Any]:
        """
        Generate prediction for a symbol at given horizon.

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            horizon: Time horizon (e.g., 60s, 5m, 1h)

        Returns:
            Prediction dict with prob_up, confidence, model name
        """
        pass


class StubSine(BaseModel):
    """Stub model using sine wave for testing."""

    name = "stub-sine"

    async def predict(self, symbol: str, horizon: str) -> dict[str, Any]:
        """Generate sine-wave based prediction."""
        t = time.time()
        # Oscillate between 0.1 and 0.9
        score = 0.5 + 0.4 * math.sin(t / 30.0)
        prob_up = max(0.0, min(1.0, score))

        return {
            "ok": True,
            "symbol": symbol,
            "horizon": horizon,
            "prob_up": prob_up,
            "confidence": 0.6,
            "model": self.name,
            "timestamp": int(t),
            "note": "Stub model for testing",
            "staleness_s": 999.0,  # Stub has no real data
            "fallback": True,
        }


class SkopsLocal(BaseModel):
    """Local scikit-learn/skops model."""

    name = "skops-local"

    def __init__(self, path: str | None = None):
        self.path = path or os.getenv("MODEL_PATH", "ops/models/model.skops")
        self._clf = None

        if os.path.exists(self.path):
            try:
                import joblib

                self._clf = joblib.load(self.path)
                print(f"✅ Loaded model from {self.path}")
            except Exception as e:
                print(f"⚠️  Failed to load model from {self.path}: {e}")
                self._clf = None
        else:
            print(f"⚠️  Model file not found: {self.path}")

    async def predict(self, symbol: str, horizon: str) -> dict[str, Any]:
        """
        Generate prediction using local model with real features from TimescaleDB.
        Silent fallback to stub-sine if data unavailable.
        """
        # Try features_v2 first, fallback to features
        try:
            from .features_v2 import load_features_v2

            feature_result = await load_features_v2(symbol, lookback=300)
        except ImportError:
            from .features import load_features

            features = await load_features(symbol, lookback=300)
            feature_result = {
                "ok": features is not None,
                "features": features,
                "staleness_s": 0.0 if features else 999.0,
                "error": None if features else "No data",
            }

        # Silent fallback: if no data, use stub-sine
        if not feature_result or not feature_result.get("ok"):
            fallback_model = PROVIDERS["stub-sine"]
            result = await fallback_model.predict(symbol, horizon)
            result["fallback"] = True
            result["fallback_reason"] = (
                feature_result.get("error") if feature_result else "No data"
            )
            result["note"] = f"⚠️ Fallback: {result['fallback_reason']}"
            return result

        features = feature_result.get("features")
        staleness = feature_result.get("staleness_s", 0.0)

        if self._clf:
            try:
                # Use real features for prediction
                proba = self._clf.predict_proba([features])
                prob_up = float(proba[0][1])
                confidence = 0.7
                note = f"✅ Real model (staleness: {staleness:.1f}s)"
            except Exception as e:
                print(f"⚠️  Model prediction failed: {e}")
                # Silent fallback
                fallback_model = PROVIDERS["stub-sine"]
                result = await fallback_model.predict(symbol, horizon)
                result["fallback"] = True
                result["fallback_reason"] = f"Model error: {e}"
                return result
        else:
            # Model not loaded - fallback
            fallback_model = PROVIDERS["stub-sine"]
            result = await fallback_model.predict(symbol, horizon)
            result["fallback"] = True
            result["fallback_reason"] = "Model file not found"
            return result

        return {
            "ok": True,
            "symbol": symbol,
            "horizon": horizon,
            "prob_up": prob_up,
            "confidence": confidence,
            "model": self.name,
            "timestamp": int(time.time()),
            "note": note,
            "staleness_s": staleness,
            "fallback": False,
        }


# Registry of available model providers
PROVIDERS: dict[str, BaseModel] = {
    "stub-sine": StubSine(),
    "skops-local": SkopsLocal(),
}


def get_model(name: str | None = None) -> BaseModel:
    """
    Get model provider by name.

    Args:
        name: Model name (defaults to stub-sine if not found)

    Returns:
        Model provider instance
    """
    if name and name in PROVIDERS:
        return PROVIDERS[name]
    return PROVIDERS["stub-sine"]

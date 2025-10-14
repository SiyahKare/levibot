"""Production LightGBM inference wrapper with thread-safe singleton."""

from __future__ import annotations

import threading
from typing import Optional

import joblib


class LGBMProd:
    """Thread-safe singleton wrapper for production LGBM inference."""

    _lock = threading.Lock()
    _model: Optional[any] = None
    _model_path: Optional[str] = None

    @classmethod
    def load(cls, path: str = "backend/data/models/best_lgbm.pkl"):
        """
        Load model (once, thread-safe).

        Args:
            path: Path to joblib-serialized model

        Returns:
            Loaded model instance
        """
        with cls._lock:
            if cls._model is None or cls._model_path != path:
                cls._model = joblib.load(path)
                cls._model_path = path
        return cls._model

    @classmethod
    def predict_proba_up(cls, features: dict[str, float]) -> float:
        """
        Predict probability of price going up.

        Args:
            features: Dictionary with feature values
                     {close, ret1, sma20_gap, sma50_gap, vol_z}

        Returns:
            Probability (0.0 - 1.0) of upward price movement
        """
        model = cls.load()

        # Feature vector in expected order
        x = [
            [
                features.get("close", 0.0),
                features.get("ret1", 0.0),
                features.get("sma20_gap", 0.0),
                features.get("sma50_gap", 0.0),
                features.get("vol_z", 0.0),
            ]
        ]

        # LightGBM predict returns raw score for binary
        proba = model.predict(x, num_iteration=getattr(model, "best_iteration", None))

        return float(proba[0])


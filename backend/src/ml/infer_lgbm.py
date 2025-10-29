"""Production LightGBM inference wrapper with thread-safe singleton."""

from __future__ import annotations

import threading
from pathlib import Path

import joblib


class LGBMProd:
    """Thread-safe singleton wrapper for production LGBM inference."""

    _lock = threading.Lock()
    _model: any | None = None
    _model_path: str | None = None

    @classmethod
    def load(cls, path: str = "backend/data/models/best_lgbm.pkl"):
        """
        Load model (once, thread-safe).

        Args:
            path: Path to joblib-serialized model (relative to project root or absolute)

        Returns:
            Loaded model instance
        """
        with cls._lock:
            if cls._model is None or cls._model_path != path:
                # Resolve path: try relative to /app (Docker) or as-is
                resolved_path = Path(path)
                if not resolved_path.exists():
                    # Try relative to /app in Docker
                    resolved_path = Path(f"/app/{path}")
                if not resolved_path.exists():
                    # Try data/models (relative to /app)
                    resolved_path = Path("data/models") / Path(path).name

                cls._model = joblib.load(str(resolved_path))
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
        try:
            proba = model.predict(
                x, num_iteration=getattr(model, "best_iteration", None)
            )
        except TypeError:
            # Fallback for models that don't support num_iteration
            proba = model.predict(x)

        return float(proba[0])

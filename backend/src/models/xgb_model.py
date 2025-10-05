from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class XGBTripleBarrierModel:
    """Stub XGBoost model wrapper.

    Replace with actual xgboost.XGBClassifier; keep interface stable.
    """

    random_state: int = 42
    trained: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        self.trained = True

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.trained:
            # neutral proba
            return np.full((len(X), 2), [0.5, 0.5])
        return np.full((len(X), 2), [0.49, 0.51])

    def save(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write("stub")

    @classmethod
    def load(cls, path: str) -> "XGBTripleBarrierModel":
        return cls()



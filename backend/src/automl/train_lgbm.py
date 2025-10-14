"""
LightGBM training module with Optuna hyperparameter tuning.

Mock implementation for now - replace with real LightGBM when ready.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


def _score(X: list[dict], y: list[int], params: dict[str, Any]) -> float:
    """
    Placeholder scoring function.

    TODO: Replace with real LightGBM training + cross-validation.

    Args:
        X: Feature rows
        y: Labels
        params: Model hyperparameters

    Returns:
        Accuracy score (0-1)
    """
    correct = 0
    for i, row in enumerate(X):
        # Simple rule: combine sma20_gap + ret1
        prediction = 1 if (row.get("sma20_gap", 0) + row.get("ret1", 0)) > 0 else 0
        correct += 1 if prediction == y[i] else 0

    accuracy = correct / max(1, len(y))

    # Regularization penalty
    penalty = 0.001 * params.get("num_leaves", 31)

    return accuracy - penalty


def train_and_dump(features_path: str, out_dir: str, n_trials: int = 32) -> str:
    """
    Train LightGBM model with Optuna hyperparameter search.

    TODO: Replace with real optuna.create_study() + lgbm.train() + joblib.dump()

    Args:
        features_path: Path to features JSON
        out_dir: Output directory for model
        n_trials: Number of Optuna trials

    Returns:
        Path to saved model file
    """
    data = json.loads(Path(features_path).read_text())
    X, y = data["X"], data["y"]

    # Optuna placeholder: random search
    best_score = -1.0
    best_params = None

    for _ in range(n_trials):
        params = {
            "num_leaves": random.randint(8, 64),
            "learning_rate": random.uniform(0.01, 0.2),
            "max_depth": random.randint(3, 8),
            "min_child_samples": random.randint(10, 50),
            "subsample": random.uniform(0.6, 1.0),
            "colsample_bytree": random.uniform(0.6, 1.0),
        }

        score = _score(X, y, params)

        if score > best_score:
            best_score = score
            best_params = params

    # Save model metadata (mock)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    model_path = Path(out_dir) / "lgbm.pkl"

    model_meta = {
        "type": "lgbm_mock",
        "params": best_params,
        "score": best_score,
        "n_samples": len(y),
        "n_features": len(X[0]) if X else 0,
    }

    model_path.write_text(json.dumps(model_meta, indent=2))

    print(f"[LGBM] Trained model: score={best_score:.4f}, params={best_params}")

    return str(model_path)


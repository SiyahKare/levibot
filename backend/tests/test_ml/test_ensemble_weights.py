"""Test ensemble weight optimization."""
from __future__ import annotations

import numpy as np

from backend.src.ml.ensemble.weights import optimize_ensemble_weights


def test_ensemble_weights_sum_to_one():
    """Ensemble weights should sum to 1."""
    np.random.seed(42)

    lgbm_proba = np.random.rand(100)
    tft_proba = np.random.rand(100)
    y_true = (np.random.rand(100) > 0.5).astype(int)

    result = optimize_ensemble_weights(lgbm_proba, tft_proba, y_true, grid_resolution=5)

    weights = result["weights"]
    total = weights["lgbm"] + weights["tft"] + weights["sentiment"]

    assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"


def test_ensemble_weights_metrics():
    """Ensemble optimization should return metrics."""
    np.random.seed(42)

    lgbm_proba = np.random.rand(100)
    tft_proba = np.random.rand(100)
    y_true = (np.random.rand(100) > 0.5).astype(int)

    result = optimize_ensemble_weights(lgbm_proba, tft_proba, y_true, grid_resolution=5)

    assert "metrics" in result
    assert "accuracy" in result["metrics"]
    assert "f1" in result["metrics"]
    assert "auc_roc" in result["metrics"]
    assert 0.0 <= result["metrics"]["accuracy"] <= 1.0


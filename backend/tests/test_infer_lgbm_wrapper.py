"""Tests for LGBM inference wrapper."""

import pytest

from src.ml.infer_lgbm import LGBMProd


def test_infer_wrapper_load_predict():
    """Test inference wrapper loads and predicts (if model exists)."""
    try:
        # Attempt to load model
        LGBMProd.load("backend/data/models/best_lgbm.pkl")
        
        # If successful, test prediction
        proba = LGBMProd.predict_proba_up(
            {"close": 100, "ret1": 0, "sma20_gap": 0, "sma50_gap": 0, "vol_z": 0}
        )
        
        assert 0.0 <= proba <= 1.0, f"Invalid probability: {proba}"
        
    except FileNotFoundError:
        # Model doesn't exist yet - skip test
        pytest.skip("Model not trained yet, skipping inference test")


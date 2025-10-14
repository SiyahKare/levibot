"""Smoke tests for production LGBM training pipeline."""

import os

import numpy as np
import pandas as pd
import pytest

from src.data.feature_store import to_parquet
from src.ml.train_lgbm_prod import train_from_parquet


@pytest.mark.asyncio
async def test_train_pipeline_smoke(tmp_path, monkeypatch):
    """Test complete training pipeline with synthetic data."""
    monkeypatch.chdir(tmp_path)

    # Create synthetic small dataset
    ts = np.arange(1_700_000_000_000, 1_700_000_000_000 + 60000 * 200, 60000)
    df = pd.DataFrame(
        {
            "ts": ts,
            "close": np.linspace(100, 120, len(ts)),
            "ret1": np.random.randn(len(ts)) * 0.01,
            "sma20_gap": np.random.randn(len(ts)) * 0.5,
            "sma50_gap": np.random.randn(len(ts)) * 1.0,
            "vol_z": np.random.randn(len(ts)),
            "y": np.random.randint(0, 2, len(ts)),
        }
    )

    # Save to feature store
    pq_path = to_parquet(df, out_dir=str(tmp_path / "fs"), symbol="BTCUSDT")

    # Train with few trials for speed
    out = train_from_parquet(pq_path, val_days=1, trials=5)

    # Verify artifacts created
    assert os.path.exists(out["model"])
    assert os.path.exists(out["card"])
    # Symlink verification (works in tmp_path context)
    assert "best" in out


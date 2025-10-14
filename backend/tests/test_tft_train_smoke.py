"""Smoke test for TFT training pipeline."""

import os

import numpy as np
import pandas as pd
from src.data.feature_store import to_parquet
from src.ml.tft.train_tft_prod import train_from_parquet


def test_tft_train_smoke(tmp_path):
    """Test TFT training pipeline with synthetic data."""
    ts = np.arange(1_700_000_000_000, 1_700_000_000_000 + 60000 * 220, 60000)
    df = pd.DataFrame(
        {
            "ts": ts,
            "close": np.linspace(100, 120, len(ts)),
            "ret1": 0,
            "sma20_gap": 0,
            "sma50_gap": 0,
            "vol_z": 0,
            "y": (np.random.rand(len(ts)) > 0.5).astype(int),
        }
    )

    pq = to_parquet(df, out_dir=tmp_path / "fs", symbol="BTCUSDT")
    out = train_from_parquet(
        str(pq), lookback=16, horizon=1, val_days=7, max_epochs=1, patience=1
    )

    assert os.path.exists(out["best_pt"])
    assert os.path.exists(out["card"])


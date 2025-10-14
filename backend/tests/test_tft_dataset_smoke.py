"""Smoke tests for TFT dataset."""

import numpy as np
import pandas as pd
from src.ml.tft.dataset import SeqDataset


def test_seq_dataset_shapes():
    """Test that SeqDataset produces correct shapes."""
    df = pd.DataFrame(
        {
            "ts": np.arange(1_700_000_000_000, 1_700_000_000_000 + 60000 * 30, 60000),
            "close": np.linspace(100, 110, 30),
            "ret1": 0,
            "sma20_gap": 0,
            "sma50_gap": 0,
            "vol_z": 0,
            "y": (np.random.rand(30) > 0.5).astype(int),
        }
    )

    ds = SeqDataset(
        df, ["close", "ret1", "sma20_gap", "sma50_gap", "vol_z"], "y", lookback=8, horizon=1
    )

    assert len(ds) > 0
    x, y = ds[0]
    assert x.shape == (8, 5)
    assert isinstance(y, (int, float, np.number))


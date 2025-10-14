"""Sequence dataset for time-series with windowing and standardization."""

from __future__ import annotations

import pandas as pd
from torch.utils.data import Dataset


class SeqDataset(Dataset):
    """Time-series dataset with lookback window and forward horizon target."""

    def __init__(
        self,
        df: pd.DataFrame,
        features,
        target: str = "y",
        lookback: int = 60,
        horizon: int = 1,
        standardize: bool = True,
    ):
        """
        Create sequence dataset.

        Args:
            df: DataFrame with features and target
            features: List of feature column names
            target: Target column name
            lookback: Number of timesteps to look back (window size)
            horizon: Number of timesteps ahead for prediction
            standardize: Whether to standardize features (z-score)
        """
        self.features = list(features)
        self.target = target
        self.L = int(lookback)
        self.H = int(horizon)

        X = df[self.features].astype("float32").values
        y = df[self.target].astype("float32").values

        if standardize:
            mu = X.mean(axis=0, keepdims=True)
            sigma = X.std(axis=0, keepdims=True) + 1e-8
            X = (X - mu) / sigma

        self.X = X
        self.y = y

    def __len__(self):
        return max(0, len(self.X) - self.L - self.H + 1)

    def __getitem__(self, i):
        x = self.X[i : i + self.L]  # (L, F)
        y = self.y[i + self.L + self.H - 1]  # binary (0/1)
        return x, y


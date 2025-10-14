"""Feature store for ML training with leak-safe time-based splits."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


@dataclass
class SplitConfig:
    """Configuration for train/val/test splits."""

    val_days: int = 14
    test_days: int = 0  # Optional in this sprint


def _ensure_dir(p: str | Path) -> Path:
    """Ensure directory exists."""
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def append_parquet(df: pd.DataFrame, path: str):
    """
    Append DataFrame to Parquet file.
    
    Simple append assuming same schema (production: add schema evolution).
    """
    p = Path(path)
    table = pa.Table.from_pandas(df)

    if p.exists():
        old = pq.read_table(p)
        table = pa.concat_tables([old, table])

    pq.write_table(table, p)


def minute_features(bars: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    """
    Generate minute-bar features from OHLCV data.

    Args:
        bars: DataFrame with columns ['ts', 'open', 'high', 'low', 'close', 'volume']
              ts in milliseconds, sorted ascending
        horizon: Minutes ahead for target prediction

    Returns:
        DataFrame with features and binary target 'y'
    """
    df = bars.copy()

    # Price features
    df["ret1"] = df["close"].pct_change().fillna(0.0)
    df["sma20"] = df["close"].rolling(20, min_periods=1).mean()
    df["sma50"] = df["close"].rolling(50, min_periods=1).mean()
    df["sma20_gap"] = df["close"] - df["sma20"]
    df["sma50_gap"] = df["close"] - df["sma50"]

    # Volume features
    vol_mean = df["volume"].rolling(50, min_periods=1).mean()
    vol_std = df["volume"].rolling(50, min_periods=1).std()
    df["vol_z"] = (df["volume"] - vol_mean) / (vol_std + 1e-9)

    # Target: 1 if price goes up in `horizon` minutes, else 0
    df["y"] = (df["close"].shift(-horizon) > df["close"]).astype(int)

    # Drop NaN and reset index
    df = df.dropna().reset_index(drop=True)

    return df[["ts", "close", "ret1", "sma20_gap", "sma50_gap", "vol_z", "y"]]


def to_parquet(
    df: pd.DataFrame, out_dir: str = "backend/data/feature_store", symbol: str = "BTCUSDT"
) -> str:
    """
    Save DataFrame to Parquet file in feature store.

    Args:
        df: DataFrame with features
        out_dir: Output directory
        symbol: Symbol name

    Returns:
        Path to created Parquet file
    """
    _ensure_dir(out_dir)
    filename = Path(out_dir) / f"{symbol}.parquet"
    append_parquet(df, str(filename))
    return str(filename)


def time_based_split(
    df: pd.DataFrame, val_days: int
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split DataFrame into train/val based on time (leak-safe).

    Args:
        df: DataFrame with 'ts' column (milliseconds)
        val_days: Number of days for validation set

    Returns:
        (train_df, val_df) tuple
    """
    # Convert ts to datetime
    ts = pd.to_datetime(df["ts"], unit="ms", utc=True)

    # Calculate cutoff point
    cutoff = ts.max() - pd.Timedelta(days=val_days)

    # Split
    train = df.loc[ts <= cutoff].reset_index(drop=True)
    val = df.loc[ts > cutoff].reset_index(drop=True)

    return train, val


def guard_no_future_leak(train: pd.DataFrame, val: pd.DataFrame):
    """
    Assert no future data leakage between train and val sets.

    Raises:
        AssertionError: If train timestamps overlap with val timestamps
    """
    assert (
        train["ts"].max() < val["ts"].min()
    ), f"Leakage: train ts max ({train['ts'].max()}) >= val ts min ({val['ts'].min()})"


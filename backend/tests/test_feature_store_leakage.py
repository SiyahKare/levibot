"""Tests for feature store leakage prevention."""

import numpy as np
import pandas as pd

from src.data.feature_store import guard_no_future_leak, time_based_split


def test_time_split_no_leak():
    """Test that time-based split has no future data leakage."""
    # Create 30-day time series (ms timestamps)
    base_ts = 1_700_000_000_000  # Oct 2023
    ts = pd.Series(np.arange(base_ts, base_ts + 60 * 1000 * 60 * 24 * 30, 60_000))  # 30 days of minutes
    df = pd.DataFrame(
        {
            "ts": ts,
            "close": 1.0,
            "ret1": 0.0,
            "sma20_gap": 0.0,
            "sma50_gap": 0.0,
            "vol_z": 0.0,
            "y": 0,
        }
    )

    # Split with 7 day validation
    train, val = time_based_split(df, val_days=7)

    # Verify no leakage
    guard_no_future_leak(train, val)

    # Verify split actually happened
    assert len(train) > 0
    assert len(val) > 0
    assert len(train) + len(val) == len(df)


def test_guard_catches_leakage():
    """Test that guard_no_future_leak catches actual leakage."""
    # Create train with future timestamps
    train = pd.DataFrame({"ts": [100, 200, 300]})
    val = pd.DataFrame({"ts": [150, 250]})  # Overlaps with train!

    try:
        guard_no_future_leak(train, val)
        assert False, "Should have raised AssertionError"
    except AssertionError as e:
        assert "Leakage" in str(e)


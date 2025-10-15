"""Test drift detection metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.src.ml.tft.drift import calculate_psi, calculate_js_divergence, detect_drift


def test_psi_identical_distributions():
    """PSI should be ~0 for identical distributions."""
    data = np.random.randn(1000)
    psi = calculate_psi(data, data)

    assert psi < 0.01, f"PSI ({psi:.4f}) should be near 0 for identical distributions"


def test_psi_shifted_distributions():
    """PSI should be >0 for shifted distributions."""
    expected = np.random.randn(1000)
    actual = np.random.randn(1000) + 1.0  # Shift by 1

    psi = calculate_psi(expected, actual)

    assert psi > 0.1, f"PSI ({psi:.4f}) should be >0.1 for shifted distributions"


def test_js_divergence_identical():
    """JS divergence should be ~0 for identical distributions."""
    data = np.random.randn(1000)
    js = calculate_js_divergence(data, data)

    assert js < 0.01, f"JS ({js:.4f}) should be near 0 for identical distributions"


def test_js_divergence_different():
    """JS divergence should be >0 for different distributions."""
    p = np.random.randn(1000)
    q = np.random.randn(1000) + 2.0

    js = calculate_js_divergence(p, q)

    assert js > 0.1, f"JS ({js:.4f}) should be >0.1 for different distributions"


def test_detect_drift_no_drift():
    """Detect drift should return 'ok' for similar data."""
    train_df = pd.DataFrame(
        {
            "ts": pd.date_range("2025-01-01", periods=1000, freq="1min"),
            "close": np.random.randn(1000),
            "volume": np.random.rand(1000) * 1000,
        }
    )

    recent_df = train_df.copy()

    report = detect_drift(train_df, recent_df, feature_cols=["close", "volume"])

    assert report["status"] == "ok"
    assert report["max_psi"] < 0.1


def test_detect_drift_with_shift():
    """Detect drift should return 'alert' for shifted data."""
    train_df = pd.DataFrame(
        {
            "ts": pd.date_range("2025-01-01", periods=1000, freq="1min"),
            "close": np.random.randn(1000),
        }
    )

    recent_df = train_df.copy()
    recent_df["close"] += 3.0  # Large shift

    report = detect_drift(
        train_df, recent_df, feature_cols=["close"], psi_threshold=0.25
    )

    assert len(report["alerts"]) > 0


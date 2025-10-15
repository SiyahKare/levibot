"""Test TFT inference latency."""
from __future__ import annotations

import numpy as np
import pytest

from backend.src.ml.bench.latency import benchmark_latency
from backend.src.ml.tft.infer_tft import TFTProd


@pytest.mark.skipif(
    not TFTProd._model, reason="TFT model not loaded (skip in CI without trained model)"
)
def test_tft_latency_target():
    """Test that TFT inference meets p95 < 40ms target."""
    # Sample input
    sample_input = np.random.randn(64, 5).astype(np.float32)

    # Benchmark
    def predict_fn(x):
        return TFTProd.predict_proba_up(x)

    stats = benchmark_latency(predict_fn, sample_input, n_warmup=10, n_samples=50)

    # Check target
    assert stats["p95"] < 40, f"TFT p95 latency ({stats['p95']:.2f}ms) exceeds 40ms target!"


def test_tft_predict_proba_shape():
    """Test TFT predict_proba_up returns float."""
    sample_input = np.random.randn(64, 5).astype(np.float32)

    proba = TFTProd.predict_proba_up(sample_input)

    assert isinstance(proba, float)
    assert 0.0 <= proba <= 1.0


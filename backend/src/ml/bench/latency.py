"""
Latency benchmarking for ML models.

Measures inference time (p50, p95, p99, etc.).
"""
from __future__ import annotations

import time
from typing import Any, Callable

import numpy as np


def benchmark_latency(
    predict_fn: Callable[[Any], Any],
    input_data: Any,
    n_warmup: int = 100,
    n_samples: int = 1000,
) -> dict[str, float]:
    """
    Benchmark model inference latency.

    Args:
        predict_fn: Prediction function (e.g., model.predict)
        input_data: Sample input for prediction
        n_warmup: Number of warm-up iterations (ignored)
        n_samples: Number of samples for timing

    Returns:
        Dictionary with latency statistics (milliseconds):
        - mean, p50, p90, p95, p99, min, max
    """
    # Warm-up (JIT compilation, cache warming)
    print(f"🔥 Warming up ({n_warmup} iterations)...")
    for _ in range(n_warmup):
        _ = predict_fn(input_data)

    # Actual benchmark
    print(f"⏱️ Benchmarking ({n_samples} samples)...")
    latencies = []
    for _ in range(n_samples):
        start = time.perf_counter()
        _ = predict_fn(input_data)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)  # Convert to milliseconds

    latencies = np.array(latencies)

    stats = {
        "mean": float(np.mean(latencies)),
        "p50": float(np.percentile(latencies, 50)),
        "p90": float(np.percentile(latencies, 90)),
        "p95": float(np.percentile(latencies, 95)),
        "p99": float(np.percentile(latencies, 99)),
        "min": float(np.min(latencies)),
        "max": float(np.max(latencies)),
        "samples": n_samples,
    }

    print(f"✅ Benchmark complete:")
    print(f"   Mean: {stats['mean']:.2f} ms")
    print(f"   P50:  {stats['p50']:.2f} ms")
    print(f"   P95:  {stats['p95']:.2f} ms")
    print(f"   P99:  {stats['p99']:.2f} ms")

    return stats


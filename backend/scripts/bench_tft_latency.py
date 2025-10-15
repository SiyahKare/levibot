#!/usr/bin/env python3
"""
Benchmark TFT inference latency.

Quick script to measure TFT inference performance.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.src.ml.bench.latency import benchmark_latency
from backend.src.ml.tft.infer_tft import TFTProd


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Benchmark TFT inference latency")
    parser.add_argument("--model", type=str, default="backend/data/models/best_tft.pt")
    parser.add_argument("--warmup", type=int, default=20, help="Warmup iterations")
    parser.add_argument("--n", type=int, default=200, help="Benchmark iterations")
    parser.add_argument("--seq-len", type=int, default=64, help="Sequence length")
    parser.add_argument("--n-features", type=int, default=5, help="Number of features")

    args = parser.parse_args()

    print("🔧 Loading TFT model...")
    TFTProd.load(args.model)

    print(f"\n⏱️ Benchmarking TFT inference (warmup={args.warmup}, n={args.n})...")

    # Create sample input
    sample_input = np.random.randn(args.seq_len, args.n_features).astype(np.float32)

    # Benchmark
    def predict_fn(x):
        return TFTProd.predict_proba_up(x)

    stats = benchmark_latency(predict_fn, sample_input, n_warmup=args.warmup, n_samples=args.n)

    # Print results
    print("\n📊 Latency Results:")
    print(f"   Mean:  {stats['mean']:.2f}ms")
    print(f"   p50:   {stats['p50']:.2f}ms")
    print(f"   p90:   {stats['p90']:.2f}ms")
    print(f"   p95:   {stats['p95']:.2f}ms")
    print(f"   p99:   {stats['p99']:.2f}ms")

    # Check target
    if stats["p95"] > 40:
        print(f"\n⚠️ WARNING: p95 ({stats['p95']:.2f}ms) exceeds 40ms target!")
        return 1

    print("\n✅ Latency target met (p95 < 40ms)")
    return 0


if __name__ == "__main__":
    sys.exit(main())


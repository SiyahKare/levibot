#!/usr/bin/env python3
"""
Drift detection for TFT models.

Metrics:
- PSI (Population Stability Index)
- JS Divergence (Jensen-Shannon)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon
from scipy.stats import chi2


def calculate_psi(
    expected: np.ndarray, actual: np.ndarray, bins: int = 10
) -> float:
    """
    Calculate Population Stability Index (PSI).

    PSI < 0.1: No significant change
    0.1 < PSI < 0.25: Moderate change (investigate)
    PSI > 0.25: Significant change (retrain)

    Args:
        expected: Expected (training) distribution
        actual: Actual (recent) distribution
        bins: Number of bins for histogram

    Returns:
        PSI value
    """
    # Create bins based on expected distribution
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
    breakpoints = np.unique(breakpoints)

    # Calculate distributions
    expected_hist, _ = np.histogram(expected, bins=breakpoints)
    actual_hist, _ = np.histogram(actual, bins=breakpoints)

    # Add small epsilon to avoid division by zero
    eps = 1e-10
    expected_pct = (expected_hist + eps) / (np.sum(expected_hist) + eps * len(expected_hist))
    actual_pct = (actual_hist + eps) / (np.sum(actual_hist) + eps * len(actual_hist))

    # PSI formula
    psi = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))

    return float(psi)


def calculate_js_divergence(p: np.ndarray, q: np.ndarray, bins: int = 10) -> float:
    """
    Calculate Jensen-Shannon divergence.

    Args:
        p: First distribution
        q: Second distribution
        bins: Number of bins

    Returns:
        JS divergence (0 = identical, 1 = completely different)
    """
    # Create histograms
    min_val = min(p.min(), q.min())
    max_val = max(p.max(), q.max())
    bins_array = np.linspace(min_val, max_val, bins + 1)

    p_hist, _ = np.histogram(p, bins=bins_array, density=True)
    q_hist, _ = np.histogram(q, bins=bins_array, density=True)

    # Normalize
    eps = 1e-10
    p_hist = (p_hist + eps) / (p_hist.sum() + eps * len(p_hist))
    q_hist = (q_hist + eps) / (q_hist.sum() + eps * len(q_hist))

    # Calculate JS divergence
    js_div = jensenshannon(p_hist, q_hist)

    return float(js_div)


def detect_drift(
    train_df: pd.DataFrame,
    recent_df: pd.DataFrame,
    feature_cols: list[str] | None = None,
    psi_threshold: float = 0.25,
    js_threshold: float = 0.3,
) -> dict:
    """
    Detect drift between training and recent data.

    Args:
        train_df: Training data
        recent_df: Recent data
        feature_cols: Columns to check (None = all numeric)
        psi_threshold: PSI alert threshold
        js_threshold: JS divergence alert threshold

    Returns:
        Drift report dict
    """
    if feature_cols is None:
        feature_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()

    print(f"🔍 Checking drift for {len(feature_cols)} features...")

    results = {}
    alerts = []

    for col in feature_cols:
        if col not in recent_df.columns:
            continue

        train_vals = train_df[col].dropna().values
        recent_vals = recent_df[col].dropna().values

        if len(train_vals) < 10 or len(recent_vals) < 10:
            continue

        # PSI
        psi = calculate_psi(train_vals, recent_vals)

        # JS divergence
        js_div = calculate_js_divergence(train_vals, recent_vals)

        results[col] = {
            "psi": psi,
            "js_divergence": js_div,
            "status": "ok",
        }

        # Check thresholds
        if psi > psi_threshold:
            results[col]["status"] = "alert"
            alerts.append(f"{col}: PSI={psi:.3f} (>{psi_threshold})")

        if js_div > js_threshold:
            if results[col]["status"] != "alert":
                results[col]["status"] = "warning"
            alerts.append(f"{col}: JS={js_div:.3f} (>{js_threshold})")

    # Summary
    max_psi = max((r["psi"] for r in results.values()), default=0)
    mean_js = np.mean([r["js_divergence"] for r in results.values()]) if results else 0

    report = {
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "train_rows": len(train_df),
        "recent_rows": len(recent_df),
        "features_checked": len(results),
        "max_psi": float(max_psi),
        "mean_js": float(mean_js),
        "alerts": alerts,
        "details": results,
        "status": "alert" if alerts else "ok",
    }

    # Print summary
    print(f"📊 Drift Summary:")
    print(f"   Max PSI: {max_psi:.3f} (threshold: {psi_threshold})")
    print(f"   Mean JS: {mean_js:.3f} (threshold: {js_threshold})")
    print(f"   Status: {report['status'].upper()}")

    if alerts:
        print(f"\n⚠️ {len(alerts)} drift alerts:")
        for alert in alerts[:5]:
            print(f"   - {alert}")

    return report


def save_drift_report(report: dict, output_path: Path):
    """Save drift report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"💾 Saved drift report: {output_path}")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Detect drift in TFT training data")
    parser.add_argument("--snapshot", type=str, required=True, help="Snapshot directory")
    parser.add_argument(
        "--recent-days", type=int, default=7, help="Recent window (days)"
    )
    parser.add_argument("--output", type=str, help="Output report path")
    parser.add_argument("--psi-threshold", type=float, default=0.25, help="PSI threshold")
    parser.add_argument("--js-threshold", type=float, default=0.3, help="JS threshold")

    args = parser.parse_args()

    # Load snapshot
    snapshot_dir = Path(args.snapshot)
    manifest_path = snapshot_dir / "manifest.json"

    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"📦 Loading snapshot: {manifest['snapshot_id']}")

    # Load all data
    dfs = []
    for file_info in manifest["files"]:
        parquet_path = snapshot_dir / file_info["path"]
        df = pd.read_parquet(parquet_path)
        dfs.append(df)

    full_df = pd.concat(dfs, ignore_index=True).sort_values("ts")

    # Split into train (older 80%) and recent (last N days)
    cutoff_ts = full_df["ts"].max() - pd.Timedelta(days=args.recent_days)

    train_df = full_df[full_df["ts"] < cutoff_ts]
    recent_df = full_df[full_df["ts"] >= cutoff_ts]

    print(f"📊 Train rows: {len(train_df):,}")
    print(f"📊 Recent rows: {len(recent_df):,} (last {args.recent_days} days)")

    # Detect drift
    report = detect_drift(
        train_df,
        recent_df,
        psi_threshold=args.psi_threshold,
        js_threshold=args.js_threshold,
    )

    # Save report
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("backend/reports") / f"drift_{pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d')}.json"

    save_drift_report(report, output_path)

    # Exit code based on status
    return 1 if report["status"] == "alert" else 0


if __name__ == "__main__":
    import sys

    sys.exit(main())


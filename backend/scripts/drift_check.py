#!/usr/bin/env python3
"""
Drift Detection - PSI & KS Test

Monitors feature distribution drift and triggers alerts/retraining.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent.parent))

# Thresholds
PSI_WARNING = 0.2
PSI_CRITICAL = 0.3
KS_WARNING = 0.15
KS_CRITICAL = 0.25


def calculate_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """
    Calculate Population Stability Index.
    
    PSI = Σ (actual% - expected%) × ln(actual% / expected%)
    
    Interpretation:
        PSI < 0.1: No significant shift
        PSI 0.1-0.2: Moderate shift
        PSI > 0.2: Significant shift (retrain recommended)
    """
    # Create bins
    breakpoints = np.percentile(expected, np.linspace(0, 100, bins + 1))
    breakpoints[-1] = breakpoints[-1] + 0.001  # Ensure last value is included
    
    # Calculate distributions
    expected_percents = np.histogram(expected, bins=breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, bins=breakpoints)[0] / len(actual)
    
    # Replace zeros with small value to avoid log(0)
    expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
    actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
    
    # PSI calculation
    psi = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
    
    return float(psi)


def ks_test(expected: np.ndarray, actual: np.ndarray) -> float:
    """
    Kolmogorov-Smirnov test statistic.
    
    Measures maximum distance between CDFs.
    """
    statistic, _ = stats.ks_2samp(expected, actual)
    return float(statistic)


def check_drift(
    train_data: pl.DataFrame,
    recent_data: pl.DataFrame,
    features: list[str],
) -> dict:
    """Check drift for all features."""
    results = {}
    
    for feature in features:
        if feature not in train_data.columns or feature not in recent_data.columns:
            continue
        
        # Get arrays
        expected = train_data[feature].fill_null(0).to_numpy()
        actual = recent_data[feature].fill_null(0).to_numpy()
        
        if len(actual) < 100:  # Not enough recent data
            continue
        
        # Calculate metrics
        psi = calculate_psi(expected, actual)
        ks = ks_test(expected, actual)
        
        # Determine status
        status = "ok"
        if psi > PSI_CRITICAL or ks > KS_CRITICAL:
            status = "critical"
        elif psi > PSI_WARNING or ks > KS_WARNING:
            status = "warning"
        
        results[feature] = {
            "psi": round(psi, 4),
            "ks": round(ks, 4),
            "status": status,
        }
    
    return results


def main():
    print(f"\n{'='*70}")
    print("🔍 DRIFT DETECTION CHECK")
    print(f"{'='*70}\n")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Load registry
    registry_path = Path("backend/data/registry/model_registry.json")
    if not registry_path.exists():
        print("❌ Model registry not found")
        sys.exit(1)
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    current = registry.get("current", {})
    features = current.get("features", [])
    symbol = current.get("symbol_set", ["BTCUSDT"])[0]
    timeframe = current.get("timeframe", "15m")
    
    print(f"Symbol: {symbol}")
    print(f"Features: {len(features)}")
    
    # Load data
    features_file = Path(f"backend/data/features/{symbol}_{timeframe}_features.parquet")
    
    if not features_file.exists():
        print(f"❌ Features not found: {features_file}")
        sys.exit(1)
    
    df = pl.read_parquet(features_file).sort("timestamp")
    
    # Split: train (first 80%) vs recent (last 24h)
    split_idx = int(len(df) * 0.8)
    train_data = df[:split_idx]
    
    # Recent data (last 24 hours)
    cutoff = datetime.now() - timedelta(hours=24)
    recent_data = df.filter(pl.col("timestamp") >= cutoff)
    
    print(f"\nTrain samples: {len(train_data)}")
    print(f"Recent samples (24h): {len(recent_data)}")
    
    if len(recent_data) < 50:
        print("⚠️  Not enough recent data for drift check")
        sys.exit(0)
    
    # Check drift
    print(f"\n{'─'*70}")
    print("DRIFT ANALYSIS")
    print(f"{'─'*70}\n")
    
    drift_results = check_drift(train_data, recent_data, features)
    
    # Summary
    critical = [f for f, r in drift_results.items() if r["status"] == "critical"]
    warning = [f for f, r in drift_results.items() if r["status"] == "warning"]
    ok = [f for f, r in drift_results.items() if r["status"] == "ok"]
    
    print(f"✅ OK:       {len(ok)}")
    print(f"⚠️  Warning: {len(warning)}")
    print(f"❌ Critical: {len(critical)}")
    
    # Detail critical/warning
    if critical:
        print(f"\n{'─'*70}")
        print("🚨 CRITICAL DRIFT DETECTED:")
        print(f"{'─'*70}")
        for feature in critical:
            r = drift_results[feature]
            print(f"  {feature:20s} PSI={r['psi']:.4f}  KS={r['ks']:.4f}")
    
    if warning:
        print(f"\n{'─'*70}")
        print("⚠️  WARNING - MODERATE DRIFT:")
        print(f"{'─'*70}")
        for feature in warning:
            r = drift_results[feature]
            print(f"  {feature:20s} PSI={r['psi']:.4f}  KS={r['ks']:.4f}")
    
    # Save results
    output_dir = Path("backend/data/drift")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"drift_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output = {
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "timeframe": timeframe,
        "train_samples": len(train_data),
        "recent_samples": len(recent_data),
        "features": drift_results,
        "summary": {
            "ok": len(ok),
            "warning": len(warning),
            "critical": len(critical),
        },
    }
    
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Results saved: {output_file}")
    
    # Update Prometheus metrics
    try:
        from prometheus_client import Counter, Gauge

        from ..src.infra.metrics import registry
        
        drift_events = Counter(
            "levibot_ml_drift_events_total",
            "Drift detection events",
            ["severity"],
            registry=registry,
        )
        drift_psi = Gauge(
            "levibot_ml_drift_psi",
            "Feature drift PSI",
            ["feature"],
            registry=registry,
        )
        
        if critical:
            drift_events.labels(severity="critical").inc(len(critical))
        if warning:
            drift_events.labels(severity="warning").inc(len(warning))
        
        for feature, result in drift_results.items():
            drift_psi.labels(feature=feature).set(result["psi"])
    
    except Exception as e:
        print(f"⚠️  Could not update metrics: {e}")
    
    # Decision
    print(f"\n{'='*70}")
    if critical:
        print("🚨 RECOMMENDATION: RETRAIN MODEL IMMEDIATELY!")
        print("   PSI > 0.3 detected on critical features")
        print(f"{'='*70}\n")
        
        # Trigger kill-switch
        kill_file = Path("backend/data/ml_kill_switch.flag")
        kill_file.touch()
        print("🛑 Kill-switch ENABLED (ml_kill_switch.flag created)")
        
        sys.exit(2)  # Exit code 2 = critical drift
    
    elif warning:
        print("⚠️  RECOMMENDATION: Monitor closely, consider retraining within 48h")
        print(f"{'='*70}\n")
        sys.exit(1)  # Exit code 1 = warning
    
    else:
        print("✅ NO SIGNIFICANT DRIFT DETECTED - System healthy")
        print(f"{'='*70}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()


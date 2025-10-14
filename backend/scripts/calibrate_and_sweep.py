#!/usr/bin/env python3
"""
Calibration + Threshold Sweep

Optimize model calibration and entry/exit thresholds for max Sharpe/min MaxDD.
"""
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.isotonic import IsotonicRegression

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import lightgbm as lgb


def calculate_ece(p_pred: np.ndarray, y_true: np.ndarray, n_bins: int = 10) -> float:
    """Calculate Expected Calibration Error."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    
    for b0, b1 in zip(bins[:-1], bins[1:]):
        mask = (p_pred >= b0) & (p_pred < b1)
        if mask.sum() < 50:  # Skip bins with too few samples
            continue
        
        gap = abs(p_pred[mask].mean() - y_true[mask].mean())
        ece += gap * (mask.sum() / len(p_pred))
    
    return float(ece)


def backtest_with_thresholds(
    predictions: np.ndarray,
    returns: np.ndarray,
    entry_threshold: float = 0.55,
    exit_threshold: float = 0.48,
    fee_bps: float = 2.0,
) -> tuple[float, float, float, float]:
    """
    Backtest with specific thresholds.
    
    Returns:
        (cagr, sharpe, max_dd, final_equity)
    """
    position = 0
    equity = 1.0
    equity_curve = [equity]
    
    for i in range(len(predictions) - 2):
        # Entry/Exit logic
        prev_pos = position
        
        if position == 0 and predictions[i] > entry_threshold:
            position = 1
        elif position == 1 and predictions[i] < exit_threshold:
            position = 0
        
        # Apply fee if position changed
        if position != prev_pos:
            equity -= (fee_bps / 10000.0) * equity
        
        # Next bar return
        if position == 1:
            equity *= (1.0 + returns[i + 1])
        
        equity_curve.append(equity)
    
    # Calculate metrics
    equity_arr = np.array(equity_curve)
    
    # Annualized (15m bars)
    periods_per_year = 365 * 24 * 4
    cagr = float(equity_arr[-1] ** (periods_per_year / len(equity_arr)) - 1)
    
    # Sharpe
    returns_series = np.diff(np.log(equity_arr + 1e-9))
    sharpe = float(
        (returns_series.mean() / (returns_series.std() + 1e-9)) * np.sqrt(periods_per_year)
    )
    
    # Max Drawdown
    cummax = np.maximum.accumulate(equity_arr)
    drawdown = 1 - (equity_arr / cummax)
    max_dd = float(drawdown.max())
    
    return cagr, sharpe, max_dd, float(equity_arr[-1])


def main():
    print(f"\n{'='*70}")
    print("🎯 CALIBRATION + THRESHOLD SWEEP")
    print(f"{'='*70}\n")
    
    # Load registry
    registry_path = Path("backend/data/registry/model_registry.json")
    if not registry_path.exists():
        print("❌ Model registry not found. Train a model first.")
        return
    
    with open(registry_path) as f:
        registry = json.load(f)
    
    current = registry.get("current")
    if not current:
        print("❌ No current model in registry.")
        return
    
    print(f"📊 Model: {current.get('id', 'unknown')}")
    print(f"   Features: {len(current.get('features', []))}")
    print(f"   Metrics: {current.get('metrics')}\n")
    
    # Load model
    model_path = current["path"]
    if not Path(model_path).exists():
        print(f"❌ Model file not found: {model_path}")
        return
    
    model = lgb.Booster(model_file=model_path)
    features = current["features"]
    
    # Load features
    symbol = current.get("symbol_set", ["BTCUSDT"])[0]
    timeframe = current.get("timeframe", "15m")
    
    features_file = Path(f"backend/data/features/{symbol}_{timeframe}_features.parquet")
    if not features_file.exists():
        print(f"❌ Features not found: {features_file}")
        return
    
    df = pl.read_parquet(features_file).sort("timestamp")
    print(f"📥 Loaded {len(df)} samples\n")
    
    # Prepare data
    X = df.select(features).to_pandas()
    y = (df["label_direction"] == 1).cast(pl.Int64).to_pandas().astype(int).values
    returns = df["ret_1"].to_numpy()
    
    # Get raw predictions
    p_raw = model.predict(X)
    
    # ─────────────────────────────────────────────────────────
    # 1. CALIBRATION
    # ─────────────────────────────────────────────────────────
    print(f"{'─'*70}")
    print("🔧 STEP 1: ISOTONIC CALIBRATION")
    print(f"{'─'*70}\n")
    
    # Split: 80% train, 20% validation (temporal)
    split_idx = int(len(p_raw) * 0.8)
    
    # Fit isotonic regression
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(p_raw[:split_idx], y[:split_idx])
    
    # Calibrate all predictions
    p_calibrated = iso.transform(p_raw)
    
    # Calculate ECE
    ece_raw = calculate_ece(p_raw, y)
    ece_calibrated = calculate_ece(p_calibrated, y)
    
    print(f"  ECE (raw):        {ece_raw:.4f}")
    print(f"  ECE (calibrated): {ece_calibrated:.4f}")
    print(f"  Improvement:      {(ece_raw - ece_calibrated):.4f}\n")
    
    # ─────────────────────────────────────────────────────────
    # 2. THRESHOLD SWEEP
    # ─────────────────────────────────────────────────────────
    print(f"{'─'*70}")
    print("🔍 STEP 2: THRESHOLD OPTIMIZATION")
    print(f"{'─'*70}\n")
    
    print("Sweeping entry/exit thresholds...")
    
    best_result = None
    entry_range = np.round(np.linspace(0.52, 0.60, 17), 3)
    exit_range = np.round(np.linspace(0.40, 0.50, 21), 3)
    
    for entry in entry_range:
        for exit_t in exit_range:
            if exit_t >= entry:
                continue
            
            cagr, sharpe, max_dd, final_eq = backtest_with_thresholds(
                p_calibrated, returns, entry, exit_t
            )
            
            # Scoring: Sharpe - 3*MaxDD (aggressive penalty for drawdown)
            score = sharpe - 3 * max_dd
            
            if best_result is None or score > best_result["score"]:
                best_result = {
                    "entry": float(entry),
                    "exit": float(exit_t),
                    "cagr": cagr,
                    "sharpe": sharpe,
                    "max_dd": max_dd,
                    "final_equity": final_eq,
                    "score": float(score),
                }
    
    print("\n✅ Optimal Thresholds Found:")
    print(f"   Entry:  {best_result['entry']:.3f}")
    print(f"   Exit:   {best_result['exit']:.3f}")
    print("\n📈 Backtest Metrics:")
    print(f"   CAGR:   {best_result['cagr']:.2%}")
    print(f"   Sharpe: {best_result['sharpe']:.2f}")
    print(f"   MaxDD:  {best_result['max_dd']:.2%}")
    print(f"   Final:  {best_result['final_equity']:.4f}x\n")
    
    # ─────────────────────────────────────────────────────────
    # 3. UPDATE REGISTRY
    # ─────────────────────────────────────────────────────────
    print(f"{'─'*70}")
    print("💾 STEP 3: UPDATE REGISTRY")
    print(f"{'─'*70}\n")
    
    # Add calibration and policy to registry
    current["calibration"] = {
        "ece_raw": round(ece_raw, 4),
        "ece_calibrated": round(ece_calibrated, 4),
        "method": "isotonic",
    }
    
    current["policy"] = {
        "entry_threshold": best_result["entry"],
        "exit_threshold": best_result["exit"],
        "backtest_metrics": {
            "cagr": round(best_result["cagr"], 4),
            "sharpe": round(best_result["sharpe"], 2),
            "max_dd": round(best_result["max_dd"], 4),
        },
    }
    
    # Save registry
    registry["current"] = current
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    print(f"✅ Registry updated: {registry_path}\n")
    
    print(f"{'='*70}")
    print("🎉 CALIBRATION + SWEEP COMPLETE!")
    print(f"{'='*70}\n")
    
    print("📊 Summary:")
    print(f"   ECE:    {ece_calibrated:.4f} ({'✅ GOOD' if ece_calibrated < 0.05 else '⚠️  NEEDS WORK'})")
    print(f"   Sharpe: {best_result['sharpe']:.2f} ({'✅ GOOD' if best_result['sharpe'] > 1.0 else '⚠️  LOW'})")
    print(f"   MaxDD:  {best_result['max_dd']:.2%} ({'✅ GOOD' if best_result['max_dd'] < 0.15 else '⚠️  HIGH'})\n")


if __name__ == "__main__":
    main()


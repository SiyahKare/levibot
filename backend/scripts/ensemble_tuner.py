#!/usr/bin/env python3
"""
Ensemble Weight Auto-Tuner

Optimizes ensemble weights based on recent shadow trading performance.
"""
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).parent.parent))


def calculate_sharpe(returns: np.ndarray, periods_per_year: int = 365 * 24 * 4) -> float:
    """Calculate annualized Sharpe ratio."""
    if len(returns) < 2:
        return 0.0
    
    mean_ret = np.mean(returns)
    std_ret = np.std(returns)
    
    if std_ret == 0:
        return 0.0
    
    return float(mean_ret / std_ret * np.sqrt(periods_per_year))


def load_shadow_results(days: int = 7) -> dict:
    """Load shadow trading results from logs."""
    shadow_dir = Path("backend/data/logs/shadow")
    
    if not shadow_dir.exists():
        return {"lgbm": [], "deep": []}
    
    # Collect results from last N days
    cutoff = datetime.now() - timedelta(days=days)
    
    lgbm_returns = []
    deep_returns = []
    
    for log_file in shadow_dir.glob("*.jsonl"):
        # Parse date from filename
        try:
            date_str = log_file.stem.split("_")[-1]
            log_date = datetime.strptime(date_str, "%Y%m%d")
            
            if log_date < cutoff:
                continue
            
            # Read log
            with open(log_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        
                        if entry.get("model") == "lgbm":
                            lgbm_returns.append(entry.get("return", 0.0))
                        elif entry.get("model") == "deep":
                            deep_returns.append(entry.get("return", 0.0))
                    
                    except:
                        continue
        
        except:
            continue
    
    return {
        "lgbm": np.array(lgbm_returns),
        "deep": np.array(deep_returns),
    }


def optimize_weights(lgbm_returns: np.ndarray, deep_returns: np.ndarray) -> dict:
    """
    Optimize ensemble weights to maximize Sharpe ratio.
    
    Returns:
        {"w_lgbm": float, "w_deep": float, "sharpe": float}
    """
    if len(lgbm_returns) < 10 or len(deep_returns) < 10:
        # Not enough data, use default weights
        return {"w_lgbm": 0.5, "w_deep": 0.5, "sharpe": 0.0, "note": "insufficient_data"}
    
    # Ensure same length
    min_len = min(len(lgbm_returns), len(deep_returns))
    lgbm_returns = lgbm_returns[:min_len]
    deep_returns = deep_returns[:min_len]
    
    def objective(w):
        """Negative Sharpe (for minimization)."""
        # w[0] = weight for lgbm, (1-w[0]) = weight for deep
        ensemble_returns = w[0] * lgbm_returns + (1 - w[0]) * deep_returns
        sharpe = calculate_sharpe(ensemble_returns)
        return -sharpe  # Minimize negative Sharpe = maximize Sharpe
    
    # Optimize
    result = minimize(
        objective,
        x0=[0.5],  # Start with equal weights
        bounds=[(0.0, 1.0)],  # w ∈ [0, 1]
        method="L-BFGS-B",
    )
    
    w_lgbm = float(result.x[0])
    w_deep = 1.0 - w_lgbm
    
    # Calculate final Sharpe
    ensemble_returns = w_lgbm * lgbm_returns + w_deep * deep_returns
    sharpe = calculate_sharpe(ensemble_returns)
    
    return {
        "w_lgbm": round(w_lgbm, 3),
        "w_deep": round(w_deep, 3),
        "sharpe": round(sharpe, 2),
    }


def smooth_weights(
    new_weights: dict,
    old_weights: dict,
    alpha: float = 0.3,
) -> dict:
    """
    Apply EWMA smoothing to prevent rapid weight changes.
    
    Args:
        new_weights: Newly optimized weights
        old_weights: Previous weights
        alpha: Smoothing factor (0 = all old, 1 = all new)
    """
    return {
        "w_lgbm": round(
            alpha * new_weights["w_lgbm"] + (1 - alpha) * old_weights["w_lgbm"], 3
        ),
        "w_deep": round(
            alpha * new_weights["w_deep"] + (1 - alpha) * old_weights["w_deep"], 3
        ),
    }


def main():
    print(f"\n{'='*70}")
    print("⚖️  ENSEMBLE WEIGHT AUTO-TUNER")
    print(f"{'='*70}\n")
    print(f"Time: {datetime.now().isoformat()}")
    
    # Load shadow results
    print("\n📊 Loading shadow trading results (last 7 days)...")
    results = load_shadow_results(days=7)
    
    lgbm_returns = results["lgbm"]
    deep_returns = results["deep"]
    
    print(f"  LightGBM trades: {len(lgbm_returns)}")
    print(f"  Deep trades:     {len(deep_returns)}")
    
    if len(lgbm_returns) < 10 or len(deep_returns) < 10:
        print("\n⚠️  Not enough shadow data for optimization")
        print("   Using default weights (0.5, 0.5)")
        
        weights = {"w_lgbm": 0.5, "w_deep": 0.5, "sharpe": 0.0}
    
    else:
        # Calculate individual Sharpes
        sharpe_lgbm = calculate_sharpe(lgbm_returns)
        sharpe_deep = calculate_sharpe(deep_returns)
        
        print("\n📈 Individual Performance:")
        print(f"  LightGBM Sharpe: {sharpe_lgbm:.2f}")
        print(f"  Deep Sharpe:     {sharpe_deep:.2f}")
        
        # Optimize
        print(f"\n{'─'*70}")
        print("🔧 Optimizing ensemble weights...")
        print(f"{'─'*70}\n")
        
        new_weights = optimize_weights(lgbm_returns, deep_returns)
        
        print("  Optimal weights:")
        print(f"    LightGBM: {new_weights['w_lgbm']:.3f}")
        print(f"    Deep:     {new_weights['w_deep']:.3f}")
        print(f"    Ensemble Sharpe: {new_weights['sharpe']:.2f}")
        
        # Load old weights
        registry_path = Path("backend/data/registry/ensemble_weights.json")
        
        if registry_path.exists():
            with open(registry_path) as f:
                old_weights = json.load(f).get("current", {"w_lgbm": 0.5, "w_deep": 0.5})
            
            print("\n  Previous weights:")
            print(f"    LightGBM: {old_weights['w_lgbm']:.3f}")
            print(f"    Deep:     {old_weights['w_deep']:.3f}")
            
            # Smooth
            weights = smooth_weights(new_weights, old_weights, alpha=0.3)
            
            print("\n  Smoothed weights (α=0.3):")
            print(f"    LightGBM: {weights['w_lgbm']:.3f}")
            print(f"    Deep:     {weights['w_deep']:.3f}")
        
        else:
            weights = new_weights
    
    # Save weights
    registry_path = Path("backend/data/registry/ensemble_weights.json")
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    
    registry = {
        "current": weights,
        "updated_at": datetime.now().isoformat(),
        "history": [],
    }
    
    # Load history
    if registry_path.exists():
        with open(registry_path) as f:
            old_registry = json.load(f)
            registry["history"] = old_registry.get("history", [])
    
    # Add to history
    registry["history"].append(
        {
            "timestamp": datetime.now().isoformat(),
            "weights": weights,
        }
    )
    
    # Keep last 30 entries
    registry["history"] = registry["history"][-30:]
    
    # Save
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    print(f"\n✅ Weights saved: {registry_path}")
    
    # Update Prometheus metrics
    try:
        from prometheus_client import Gauge

        from ..src.infra.metrics import registry as prom_registry
        
        ensemble_weight = Gauge(
            "levibot_ensemble_weight",
            "Ensemble model weights",
            ["model"],
            registry=prom_registry,
        )
        
        ensemble_weight.labels(model="lgbm").set(weights["w_lgbm"])
        ensemble_weight.labels(model="deep").set(weights["w_deep"])
        
        print("✅ Prometheus metrics updated")
    
    except Exception as e:
        print(f"⚠️  Could not update metrics: {e}")
    
    print(f"\n{'='*70}")
    print("✅ ENSEMBLE TUNING COMPLETE!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()


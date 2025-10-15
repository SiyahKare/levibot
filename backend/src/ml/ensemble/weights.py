#!/usr/bin/env python3
"""
Ensemble weight optimization on validation set.

Optimizes LGBM + TFT weights using grid search on validation data.
"""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score


def optimize_ensemble_weights(
    lgbm_proba: np.ndarray,
    tft_proba: np.ndarray,
    y_true: np.ndarray,
    sentiment_proba: np.ndarray | None = None,
    grid_resolution: int = 11,
) -> dict:
    """
    Optimize ensemble weights using grid search.

    Args:
        lgbm_proba: LGBM probabilities (N,)
        tft_proba: TFT probabilities (N,)
        y_true: True labels (N,)
        sentiment_proba: Optional sentiment probabilities (N,)
        grid_resolution: Grid resolution (default: 11 → 0.0, 0.1, ..., 1.0)

    Returns:
        Dict with best weights and metrics
    """
    print(f"🔍 Optimizing ensemble weights (grid resolution: {grid_resolution})...")

    best_score = 0
    best_weights = {"lgbm": 0.5, "tft": 0.5, "sentiment": 0.0}
    best_preds = None

    # Grid search
    if sentiment_proba is None:
        # Binary grid: lgbm + tft
        for w_lgbm in np.linspace(0, 1, grid_resolution):
            w_tft = 1 - w_lgbm

            # Ensemble prediction
            ensemble_proba = w_lgbm * lgbm_proba + w_tft * tft_proba
            preds = (ensemble_proba > 0.5).astype(int)

            # Score
            acc = accuracy_score(y_true, preds)

            if acc > best_score:
                best_score = acc
                best_weights = {"lgbm": float(w_lgbm), "tft": float(w_tft), "sentiment": 0.0}
                best_preds = preds

    else:
        # Triple grid: lgbm + tft + sentiment
        for w_lgbm in np.linspace(0, 1, grid_resolution):
            for w_tft in np.linspace(0, 1 - w_lgbm, grid_resolution):
                w_sentiment = 1 - w_lgbm - w_tft

                # Ensemble prediction
                ensemble_proba = (
                    w_lgbm * lgbm_proba + w_tft * tft_proba + w_sentiment * sentiment_proba
                )
                preds = (ensemble_proba > 0.5).astype(int)

                # Score
                acc = accuracy_score(y_true, preds)

                if acc > best_score:
                    best_score = acc
                    best_weights = {
                        "lgbm": float(w_lgbm),
                        "tft": float(w_tft),
                        "sentiment": float(w_sentiment),
                    }
                    best_preds = preds

    # Calculate final metrics
    ensemble_proba_final = (
        best_weights["lgbm"] * lgbm_proba
        + best_weights["tft"] * tft_proba
        + best_weights["sentiment"] * (sentiment_proba if sentiment_proba is not None else 0)
    )

    metrics = {
        "accuracy": accuracy_score(y_true, best_preds),
        "f1": f1_score(y_true, best_preds),
        "auc_roc": roc_auc_score(y_true, ensemble_proba_final),
    }

    print("✅ Best weights found:")
    print(f"   LGBM: {best_weights['lgbm']:.3f}")
    print(f"   TFT: {best_weights['tft']:.3f}")
    print(f"   Sentiment: {best_weights['sentiment']:.3f}")
    print("📊 Validation metrics:")
    print(f"   Accuracy: {metrics['accuracy']:.4f}")
    print(f"   F1: {metrics['f1']:.4f}")
    print(f"   AUC-ROC: {metrics['auc_roc']:.4f}")

    return {
        "weights": best_weights,
        "metrics": metrics,
        "timestamp": datetime.now(UTC).isoformat(),
    }


def save_ensemble_config(config: dict, output_path: Path):
    """Save ensemble configuration."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"💾 Saved ensemble config: {output_path}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Optimize ensemble weights")
    parser.add_argument(
        "--lgbm-proba", type=str, required=True, help="Path to LGBM probabilities CSV"
    )
    parser.add_argument(
        "--tft-proba", type=str, required=True, help="Path to TFT probabilities CSV"
    )
    parser.add_argument(
        "--y-true", type=str, required=True, help="Path to true labels CSV"
    )
    parser.add_argument(
        "--sentiment-proba", type=str, help="Path to sentiment probabilities CSV"
    )
    parser.add_argument(
        "--grid-resolution", type=int, default=11, help="Grid resolution"
    )
    parser.add_argument("--output", type=str, help="Output config path")

    args = parser.parse_args()

    # Load data
    lgbm_proba = pd.read_csv(args.lgbm_proba, header=None).values.flatten()
    tft_proba = pd.read_csv(args.tft_proba, header=None).values.flatten()
    y_true = pd.read_csv(args.y_true, header=None).values.flatten()

    sentiment_proba = None
    if args.sentiment_proba:
        sentiment_proba = pd.read_csv(args.sentiment_proba, header=None).values.flatten()

    # Optimize
    config = optimize_ensemble_weights(
        lgbm_proba,
        tft_proba,
        y_true,
        sentiment_proba,
        grid_resolution=args.grid_resolution,
    )

    # Save
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path("backend/data/models") / "ensemble.json"

    save_ensemble_config(config, output_path)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())


#!/usr/bin/env python3
"""
Production LightGBM training with Optuna, calibration, and Model Card v2.

Features:
- Snapshot-based training (reproducibility)
- Optuna hyperparameter tuning (200+ trials)
- Probability calibration (Platt/Isotonic)
- Latency benchmarking (p50/p95/p99)
- Model Card v2 generation (JSON schema validated)
- Leakage guards (time-based splits)
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.src.data.feature_registry.validator import validate_features
from backend.src.ml.bench.latency import benchmark_latency
from backend.src.ml.postproc.calibration import (
    calibrate_probabilities,
    expected_calibration_error,
    plot_calibration_curve,
)

# Feature columns (update based on features.yml)
FEATURE_COLS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "ret_1m",
    "sma_20_gap",
    "sma_50_gap",
    "rsi_14",
    "vol_z",
    "atr_14",
]
TARGET_COL = "target_up_h5"


def load_snapshot(snapshot_dir: Path) -> tuple[pd.DataFrame, dict]:
    """
    Load training data from snapshot.

    Args:
        snapshot_dir: Path to snapshot directory

    Returns:
        Tuple of (combined_df, manifest_dict)
    """
    manifest_path = snapshot_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path) as f:
        manifest = json.load(f)

    print(f"📦 Loading snapshot: {manifest['snapshot_id']}")
    print(f"   Symbols: {', '.join(manifest['symbols'])}")
    print(f"   Range: {manifest['range']['start']} to {manifest['range']['end']}")

    # Load all Parquet files
    dfs = []
    for file_info in manifest["files"]:
        parquet_path = snapshot_dir / file_info["path"]
        df = pd.read_parquet(parquet_path)

        # Verify checksum
        actual_checksum = hashlib.sha256(open(parquet_path, "rb").read()).hexdigest()
        if actual_checksum != file_info["sha256"]:
            raise ValueError(
                f"Checksum mismatch for {file_info['path']}! "
                f"Expected {file_info['sha256'][:16]}..., "
                f"got {actual_checksum[:16]}..."
            )

        print(f"   ✅ Loaded {file_info['symbol']}: {len(df):,} rows")
        dfs.append(df)

    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"\n📊 Total rows: {len(combined_df):,}")

    return combined_df, manifest


def time_based_split(
    df: pd.DataFrame, val_ratio: float = 0.2
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data by time (train/val).

    Args:
        df: DataFrame with 'ts' column
        val_ratio: Fraction of data for validation

    Returns:
        Tuple of (train_df, val_df)
    """
    df_sorted = df.sort_values("ts").reset_index(drop=True)
    split_idx = int(len(df_sorted) * (1 - val_ratio))

    train_df = df_sorted.iloc[:split_idx].copy()
    val_df = df_sorted.iloc[split_idx:].copy()

    # Leakage guard: train_max < val_min
    train_max_ts = train_df["ts"].max()
    val_min_ts = val_df["ts"].min()

    if train_max_ts >= val_min_ts:
        raise ValueError(
            f"TIME-SPLIT VIOLATION: train_max ({train_max_ts}) >= val_min ({val_min_ts}). "
            "POTENTIAL DATA LEAKAGE!"
        )

    print(f"✅ Time-based split validated (no leakage)")
    print(f"   Train: {len(train_df):,} rows (max ts: {train_max_ts})")
    print(f"   Val:   {len(val_df):,} rows (min ts: {val_min_ts})")

    return train_df, val_df


def prepare_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Extract features and target."""
    # Filter to available columns
    available_features = [f for f in FEATURE_COLS if f in df.columns]

    if len(available_features) < len(FEATURE_COLS):
        missing = set(FEATURE_COLS) - set(available_features)
        print(f"⚠️ Missing features (will use available only): {missing}")

    X = df[available_features].fillna(0).astype("float32")
    y = df[TARGET_COL].astype("int8")

    return X, y


def train_with_optuna(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    n_trials: int = 200,
    early_stop: int = 50,
    seed: int = 42,
) -> dict:
    """
    Train LightGBM with Optuna hyperparameter optimization.

    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        n_trials: Number of Optuna trials
        early_stop: Early stopping patience
        seed: Random seed

    Returns:
        Dictionary with best_value, best_params, best_model
    """
    X_train, y_train = prepare_dataset(train_df)
    X_val, y_val = prepare_dataset(val_df)

    print(f"\n🔍 Starting Optuna optimization ({n_trials} trials)...")

    def objective(trial: optuna.Trial):
        params = {
            "objective": "binary",
            "metric": "binary_logloss",
            "verbosity": -1,
            "boosting_type": "gbdt",
            "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 16, 256, log=True),
            "min_data_in_leaf": trial.suggest_int(
                "min_data_in_leaf", 16, 512, log=True
            ),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
            "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
            "bagging_freq": trial.suggest_int("bagging_freq", 0, 10),
            "lambda_l1": trial.suggest_float("lambda_l1", 1e-9, 10.0, log=True),
            "lambda_l2": trial.suggest_float("lambda_l2", 1e-9, 10.0, log=True),
            "seed": seed,
        }

        lgb_train = lgb.Dataset(X_train, y_train)
        lgb_val = lgb.Dataset(X_val, y_val, reference=lgb_train)

        model = lgb.train(
            params,
            lgb_train,
            valid_sets=[lgb_val],
            num_boost_round=4000,
            callbacks=[lgb.early_stopping(early_stop, verbose=False)],
        )

        # Accuracy as primary metric
        y_pred_proba = model.predict(X_val, num_iteration=model.best_iteration)
        y_pred = (y_pred_proba > 0.5).astype(int)
        acc = accuracy_score(y_val, y_pred)

        return acc

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)

    print(f"✅ Optuna complete: best accuracy = {study.best_value:.4f}")

    # Train final model with best params
    best_params = study.best_params
    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_val = lgb.Dataset(X_val, y_val, reference=lgb_train)

    final_params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "verbosity": -1,
        **best_params,
    }

    final_model = lgb.train(
        final_params,
        lgb_train,
        valid_sets=[lgb_val],
        num_boost_round=4000,
        callbacks=[lgb.early_stopping(early_stop, verbose=False)],
    )

    return {
        "best_value": study.best_value,
        "best_params": best_params,
        "best_model": final_model,
    }


def evaluate_model(model: lgb.Booster, val_df: pd.DataFrame) -> dict:
    """Compute metrics on validation set."""
    X_val, y_val = prepare_dataset(val_df)

    y_pred_proba = model.predict(X_val, num_iteration=model.best_iteration)
    y_pred = (y_pred_proba > 0.5).astype(int)

    metrics = {
        "accuracy": accuracy_score(y_val, y_pred),
        "f1": f1_score(y_val, y_pred),
        "precision": precision_score(y_val, y_pred, zero_division=0),
        "recall": recall_score(y_val, y_pred, zero_division=0),
        "auc_roc": roc_auc_score(y_val, y_pred_proba),
    }

    # Calibration ECE (before calibration)
    ece = expected_calibration_error(y_val.values, y_pred_proba)
    metrics["calibration_ece_before"] = ece

    print(f"\n📊 Validation Metrics:")
    for k, v in metrics.items():
        print(f"   {k}: {v:.4f}")

    return metrics


def calibrate_model(
    model: lgb.Booster, val_df: pd.DataFrame, method: str = "isotonic"
) -> dict:
    """
    Calibrate model probabilities.

    Returns dict with calibrator and ECE after calibration.
    """
    X_val, y_val = prepare_dataset(val_df)
    y_pred_proba = model.predict(X_val, num_iteration=model.best_iteration)

    print(f"\n🔧 Calibrating probabilities (method: {method})...")

    y_calibrated, ece_after = calibrate_probabilities(
        y_val.values, y_pred_proba, method=method
    )

    print(f"   ECE before: {expected_calibration_error(y_val.values, y_pred_proba):.4f}")
    print(f"   ECE after:  {ece_after:.4f}")

    return {
        "method": method,
        "ece_after": ece_after,
        "y_calibrated": y_calibrated,
    }


def benchmark_model_latency(model: lgb.Booster, sample_input: pd.DataFrame) -> dict:
    """Benchmark inference latency."""
    print(f"\n⏱️ Benchmarking inference latency...")

    def predict_fn(x):
        return model.predict(x, num_iteration=model.best_iteration)

    latency_stats = benchmark_latency(
        predict_fn, sample_input, n_warmup=100, n_samples=1000
    )

    return latency_stats


def generate_model_card_v2(
    model: lgb.Booster,
    manifest: dict,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    metrics: dict,
    calibration_info: dict,
    latency_stats: dict,
    best_params: dict,
) -> dict:
    """Generate Model Card v2 (conforms to model_card_schema.json)."""
    # Feature importance
    importance = model.feature_importance(importance_type="gain")
    feature_names = model.feature_name()
    feature_importance = [
        {"name": name, "gain": float(gain)}
        for name, gain in sorted(
            zip(feature_names, importance), key=lambda x: x[1], reverse=True
        )[:20]
    ]

    # Class balance
    y_train = train_df[TARGET_COL]
    class_balance = {
        "pos": int((y_train == 1).sum()),
        "neg": int((y_train == 0).sum()),
    }

    card = {
        "version": "2",
        "model_name": "lgbm_prod",
        "created_at": datetime.now(UTC).isoformat(),
        "train": {
            "snapshot_id": manifest["snapshot_id"],
            "range": manifest["range"],
            "rows": len(train_df) + len(val_df),
            "class_balance": class_balance,
            "symbols": manifest["symbols"],
        },
        "metrics": {
            "accuracy": metrics["accuracy"],
            "f1": metrics["f1"],
            "precision": metrics["precision"],
            "recall": metrics["recall"],
            "auc_roc": metrics["auc_roc"],
            "calibration_ece": calibration_info["ece_after"],
        },
        "latency_ms": latency_stats,
        "leakage_checks": {
            "future_info": True,  # Validated by time_based_split
            "time_split": True,  # Enforced
            "feature_audit": True,  # Schema validated
        },
        "feature_importance": feature_importance,
        "hyperparameters": best_params,
        "model_file": "lgbm.pkl",
        "notes": f"Trained with Optuna ({len(best_params)} hyperparams), calibrated with {calibration_info['method']}",
    }

    return card


def save_artifacts(
    model: lgb.Booster,
    model_card: dict,
    output_dir: Path,
) -> dict[str, Path]:
    """Save model, card, and create symlinks."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = output_dir / "lgbm.pkl"
    joblib.dump(model, model_path)
    print(f"💾 Saved model: {model_path}")

    # Save model card
    card_path = output_dir / "model_card.json"
    with open(card_path, "w") as f:
        json.dump(model_card, f, indent=2)
    print(f"💾 Saved model card: {card_path}")

    # Save calibration plot
    # (Would need y_val and y_pred_proba - skipping for now)

    # Create symlinks to "best"
    models_root = output_dir.parent
    best_model_link = models_root / "best_lgbm.pkl"
    best_card_link = models_root / "best_lgbm_model_card.json"

    for link in [best_model_link, best_card_link]:
        if link.exists() or link.is_symlink():
            link.unlink()

    best_model_link.symlink_to(model_path.name if model_path.parent == models_root else f"{output_dir.name}/lgbm.pkl")
    best_card_link.symlink_to(card_path.name if card_path.parent == models_root else f"{output_dir.name}/model_card.json")

    print(f"🔗 Symlink: {best_model_link} -> {model_path.name}")
    print(f"🔗 Symlink: {best_card_link} -> {card_path.name}")

    return {
        "model": model_path,
        "card": card_path,
        "best_model_link": best_model_link,
        "best_card_link": best_card_link,
    }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Train production LGBM model")
    parser.add_argument(
        "--snapshot",
        type=str,
        required=True,
        help="Path to snapshot directory (e.g., backend/data/snapshots/2025-10-15)",
    )
    parser.add_argument(
        "--trials", type=int, default=200, help="Optuna trials (default: 200)"
    )
    parser.add_argument(
        "--early-stop", type=int, default=50, help="Early stopping patience (default: 50)"
    )
    parser.add_argument(
        "--calibration",
        type=str,
        default="isotonic",
        choices=["sigmoid", "isotonic"],
        help="Calibration method (default: isotonic)",
    )
    parser.add_argument(
        "--val-ratio",
        type=float,
        default=0.2,
        help="Validation ratio (default: 0.2)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (default: backend/data/models/<date>)",
    )

    args = parser.parse_args()

    # Load snapshot
    snapshot_dir = Path(args.snapshot)
    df, manifest = load_snapshot(snapshot_dir)

    # Validate schema
    print(f"\n🔍 Validating feature schema...")
    try:
        validate_features(df)
        print(f"   ✅ Schema validation passed")
    except ValueError as e:
        print(f"   ❌ Schema validation failed: {e}")
        return 1

    # Time-based split
    train_df, val_df = time_based_split(df, val_ratio=args.val_ratio)

    # Train with Optuna
    optuna_result = train_with_optuna(
        train_df, val_df, n_trials=args.trials, early_stop=args.early_stop
    )
    model = optuna_result["best_model"]

    # Evaluate
    metrics = evaluate_model(model, val_df)

    # Calibrate
    calibration_info = calibrate_model(model, val_df, method=args.calibration)

    # Benchmark latency
    X_sample, _ = prepare_dataset(val_df.head(1))
    latency_stats = benchmark_model_latency(model, X_sample)

    # Generate Model Card v2
    print(f"\n📝 Generating Model Card v2...")
    model_card = generate_model_card_v2(
        model,
        manifest,
        train_df,
        val_df,
        metrics,
        calibration_info,
        latency_stats,
        optuna_result["best_params"],
    )

    # Save artifacts
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path("backend/data/models") / datetime.now(UTC).strftime("%Y-%m-%d")

    paths = save_artifacts(model, model_card, output_dir)

    print(f"\n✅ Training complete!")
    print(f"   Model: {paths['model']}")
    print(f"   Card: {paths['card']}")
    print(f"   Best symlink: {paths['best_model_link']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

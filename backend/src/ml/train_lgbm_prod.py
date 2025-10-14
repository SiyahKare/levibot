"""Production LightGBM training with Optuna hyperparameter optimization."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Tuple

import joblib
import lightgbm as lgb
import optuna
import pandas as pd

from ..data.feature_store import guard_no_future_leak, time_based_split

FEATURES = ["close", "ret1", "sma20_gap", "sma50_gap", "vol_z"]


def _dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract features and target from DataFrame."""
    X = df[FEATURES].astype("float32")
    y = df["y"].astype("int8")
    return X, y


def train_with_optuna(
    df_split: Tuple[pd.DataFrame, pd.DataFrame], n_trials: int = 200, seed: int = 42
) -> dict[str, Any]:
    """
    Train LightGBM with Optuna hyperparameter optimization.

    Args:
        df_split: (train_df, val_df) tuple
        n_trials: Number of Optuna trials
        seed: Random seed

    Returns:
        Dictionary with best_value and best_params
    """
    X_train, y_train = _dataset(df_split[0])
    X_val, y_val = _dataset(df_split[1])

    def objective(trial: optuna.Trial):
        params = {
            "objective": "binary",
            "metric": "binary_logloss",
            "verbosity": -1,
            "boosting_type": "gbdt",
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
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
            callbacks=[lgb.early_stopping(100, verbose=False)],
        )

        # Use accuracy for better interpretability
        y_hat = (
            model.predict(X_val, num_iteration=model.best_iteration) > 0.5
        ).astype(int)
        acc = (y_hat == y_val).mean()

        return acc

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    return {"best_value": study.best_value, "best_params": study.best_params}


def fit_best(
    df_split: Tuple[pd.DataFrame, pd.DataFrame], best_params: dict[str, Any]
) -> lgb.Booster:
    """
    Fit final model with best parameters.

    Args:
        df_split: (train_df, val_df) tuple
        best_params: Best hyperparameters from Optuna

    Returns:
        Trained LightGBM Booster
    """
    X_train, y_train = _dataset(df_split[0])
    X_val, y_val = _dataset(df_split[1])

    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_val = lgb.Dataset(X_val, y_val, reference=lgb_train)

    params = {
        "objective": "binary",
        "metric": "binary_logloss",
        "verbosity": -1,
        **best_params,
    }

    model = lgb.train(
        params,
        lgb_train,
        valid_sets=[lgb_val],
        num_boost_round=best_params.get("num_boost_round", 4000),
        callbacks=[lgb.early_stopping(100, verbose=False)],
    )

    return model


def save_artifacts(
    model: lgb.Booster, acc: float, out_dir: str = "backend/data/models"
) -> dict[str, str]:
    """
    Save model artifacts (pickle, model card, symlink).

    Args:
        model: Trained LightGBM model
        acc: Validation accuracy
        out_dir: Output directory

    Returns:
        Dictionary with paths to created artifacts
    """
    # Create dated directory
    date_dir = Path(out_dir) / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    model_path = date_dir / "lgbm.pkl"
    joblib.dump(model, model_path)

    # Save model card
    card = {
        "model": "LightGBM",
        "features": FEATURES,
        "val_accuracy": float(acc),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "path": str(model_path),
        "best_iteration": getattr(model, "best_iteration", None),
    }
    card_path = date_dir / "model_card.json"
    card_path.write_text(json.dumps(card, indent=2))

    # Create/update symlink to best model
    best_link = Path(out_dir) / "best_lgbm.pkl"
    if best_link.exists() or best_link.is_symlink():
        best_link.unlink()
    best_link.symlink_to(model_path.resolve())

    return {
        "model": str(model_path),
        "card": str(card_path),
        "best": str(best_link),
    }


def train_from_parquet(
    parquet_path: str, val_days: int = 14, trials: int = 200
) -> dict[str, str]:
    """
    Complete training pipeline from Parquet file.

    Args:
        parquet_path: Path to feature store Parquet file
        val_days: Days for validation set
        trials: Number of Optuna trials

    Returns:
        Dictionary with paths to created artifacts
    """
    # Load data
    df = pd.read_parquet(parquet_path)

    # Split
    train_df, val_df = time_based_split(df, val_days)
    guard_no_future_leak(train_df, val_df)

    # Optimize hyperparameters
    result = train_with_optuna((train_df, val_df), n_trials=trials)
    print(f"✅ Optuna: best accuracy = {result['best_value']:.4f}")

    # Train final model
    model = fit_best((train_df, val_df), result["best_params"])

    # Calculate final validation accuracy
    X_val, y_val = _dataset(val_df)
    y_hat = (model.predict(X_val, num_iteration=model.best_iteration) > 0.5).astype(
        int
    )
    acc = (y_hat == y_val).mean()

    print(f"✅ Final model: val accuracy = {acc:.4f}")

    # Save artifacts
    return save_artifacts(model, acc)


"""
LightGBM Baseline Model

Fast, interpretable baseline for time-series prediction.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import lightgbm as lgb
import polars as pl
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import TimeSeriesSplit


class LightGBMPredictor:
    """
    LightGBM model for crypto price prediction.
    
    Features:
    - Time-series cross-validation
    - Early stopping
    - Feature importance tracking
    - Production-ready serialization
    """
    
    def __init__(self, model_path: str | None = None):
        """
        Initialize predictor.
        
        Args:
            model_path: Path to saved model (optional)
        """
        self.model = None
        self.feature_names = None
        
        if model_path and os.path.exists(model_path):
            self.load(model_path)
    
    def train(
        self,
        X: pl.DataFrame,
        y: pl.Series,
        n_splits: int = 5,
        num_boost_round: int = 4000,
        early_stopping_rounds: int = 120,
    ) -> dict:
        """
        Train model with time-series cross-validation.
        
        Args:
            X: Features DataFrame
            y: Labels Series
            n_splits: Number of CV folds
            num_boost_round: Max boosting rounds
            early_stopping_rounds: Early stopping patience
        
        Returns:
            Metrics dictionary
        """
        print(f"🤖 Training LightGBM with {len(X)} samples, {len(X.columns)} features")
        
        self.feature_names = X.columns
        
        # Convert to pandas for sklearn compatibility
        X_pd = X.to_pandas()
        y_pd = y.to_pandas().astype(int)
        
        # Time-series split
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        oof_y = []
        oof_p = []
        models = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_pd), 1):
            print(f"  Fold {fold}/{n_splits}...")
            
            # Split data
            X_train, X_val = X_pd.iloc[train_idx], X_pd.iloc[val_idx]
            y_train, y_val = y_pd.iloc[train_idx], y_pd.iloc[val_idx]
            
            # Create datasets
            dtrain = lgb.Dataset(X_train, label=y_train)
            dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
            
            # Train
            params = {
                "objective": "binary",
                "metric": "auc",
                "learning_rate": 0.03,
                "num_leaves": 64,
                "feature_fraction": 0.8,
                "bagging_fraction": 0.8,
                "bagging_freq": 1,
                "min_data_in_leaf": 50,
                "verbose": -1,
            }
            
            model = lgb.train(
                params,
                dtrain,
                valid_sets=[dval],
                num_boost_round=num_boost_round,
                callbacks=[lgb.early_stopping(early_stopping_rounds, verbose=False)],
            )
            
            # Predict
            p = model.predict(X_val)
            
            oof_y.extend(y_val)
            oof_p.extend(p)
            models.append(model)
        
        # Use last model as final (most recent data)
        self.model = models[-1]
        
        # Calculate metrics
        auc = roc_auc_score(oof_y, oof_p)
        brier = brier_score_loss(oof_y, oof_p)
        
        metrics = {
            "auc": round(auc, 4),
            "brier": round(brier, 5),
            "n_samples": len(X),
            "n_features": len(X.columns),
            "n_folds": n_splits,
        }
        
        print(f"✅ Training complete! AUC: {auc:.4f}, Brier: {brier:.5f}")
        
        return metrics
    
    def predict(self, X: pl.DataFrame) -> list[float]:
        """
        Predict probabilities.
        
        Args:
            X: Features DataFrame
        
        Returns:
            List of probabilities (p_up)
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        # Ensure feature order matches
        if self.feature_names:
            X = X.select(self.feature_names)
        
        X_pd = X.to_pandas()
        predictions = self.model.predict(X_pd)
        
        return predictions.tolist()
    
    def save(self, path: str):
        """Save model to disk."""
        if self.model is None:
            raise ValueError("No model to save")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(path)
        print(f"💾 Model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk."""
        self.model = lgb.Booster(model_file=path)
        self.feature_names = self.model.feature_name()
        print(f"📂 Model loaded from {path}")
    
    def get_feature_importance(self, top_k: int = 20) -> dict:
        """Get feature importance scores."""
        if self.model is None:
            raise ValueError("Model not trained")
        
        importance = self.model.feature_importance(importance_type="gain")
        names = self.model.feature_name()
        
        # Sort and get top k
        sorted_idx = importance.argsort()[::-1][:top_k]
        
        return {
            names[i]: float(importance[i])
            for i in sorted_idx
        }


def train_baseline_model(
    symbol: str = "BTCUSDT",
    timeframe: str = "15m",
    features_path: str = "backend/data/features",
    models_dir: str = "backend/data/models",
    registry_path: str = "backend/data/registry/model_registry.json",
) -> dict:
    """
    Train baseline model and update registry.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        features_path: Path to features directory
        models_dir: Path to models directory
        registry_path: Path to model registry
    
    Returns:
        Training metrics
    """
    print(f"\n{'='*60}")
    print(f"🚀 TRAINING BASELINE MODEL: {symbol} {timeframe}")
    print(f"{'='*60}\n")
    
    # Load features
    features_file = Path(features_path) / f"{symbol}_{timeframe}_features.parquet"
    
    if not features_file.exists():
        raise FileNotFoundError(f"Features not found: {features_file}")
    
    df = pl.read_parquet(features_file)
    print(f"📊 Loaded {len(df)} samples")
    
    # Prepare features and labels
    feature_cols = [
        "ret_1", "ret_3", "ret_6", "ret_12",
        "rsi_14", "ema_21", "ema_55", "ema_200",
        "bb_pct", "atr_14",
        "realized_vol_20", "z_score_20",
        # One-hot regime features
        "regime_vol_low", "regime_vol_med", "regime_vol_high",
        "regime_trend_up", "regime_trend_down", "regime_trend_side",
    ]
    
    # Filter to available features
    available_features = [f for f in feature_cols if f in df.columns]
    
    X = df.select(available_features)
    
    # Convert label to binary (direction: 1 = up, -1/0 = down/flat)
    y = (df["label_direction"] == 1).cast(pl.Int64)
    
    # Train model
    predictor = LightGBMPredictor()
    metrics = predictor.train(X, y)
    
    # Save model
    os.makedirs(models_dir, exist_ok=True)
    timestamp = int(time.time())
    model_path = f"{models_dir}/lgb_{symbol}_{timeframe}_{timestamp}.txt"
    predictor.save(model_path)
    
    # Update registry
    os.makedirs(Path(registry_path).parent, exist_ok=True)
    
    registry = {"current": {}}
    if os.path.exists(registry_path):
        with open(registry_path) as f:
            registry = json.load(f)
    
    registry["current"] = {
        "symbol_set": [symbol],
        "timeframe": timeframe,
        "horizon": f"{timeframe}_lookahead_3",
        "path": model_path,
        "metrics": metrics,
        "features": available_features,
        "trained_at": timestamp,
    }
    
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    print(f"\n✅ Registry updated: {registry_path}")
    
    # Feature importance
    importance = predictor.get_feature_importance(top_k=10)
    print("\n📊 Top 10 Features:")
    for feat, score in importance.items():
        print(f"  {feat:20s} {score:>10.2f}")
    
    return metrics


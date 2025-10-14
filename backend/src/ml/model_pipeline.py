"""
ML Model Pipeline - Training, inference, and model registry
Supports LightGBM, XGBoost, and PyTorch models
"""
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit


@dataclass
class ModelMetadata:
    """Model metadata for registry"""
    model_id: str
    model_type: Literal["lightgbm", "xgboost", "pytorch"]
    version: str
    created_at: str
    features: list[str]
    target: str
    metrics: dict
    hyperparams: dict
    training_samples: int


class ModelRegistry:
    """
    Model registry for versioning and deployment
    
    Structure:
    models/
      production/
        model_v1.0.0.pkl
        metadata.json
      staging/
        model_v1.1.0.pkl
        metadata.json
      archive/
        ...
    """
    
    def __init__(self, base_path: str = "backend/data/models"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        for subdir in ["production", "staging", "archive"]:
            (self.base_path / subdir).mkdir(exist_ok=True)
    
    def save_model(
        self,
        model: any,
        metadata: ModelMetadata,
        stage: Literal["production", "staging"] = "staging"
    ):
        """Save model with metadata"""
        stage_path = self.base_path / stage
        
        # Save model
        model_path = stage_path / f"model_{metadata.version}.pkl"
        joblib.dump(model, model_path)
        
        # Save metadata
        metadata_path = stage_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata.__dict__, f, indent=2)
        
        print(f"✅ Model saved: {stage}/{metadata.version}")
    
    def load_model(
        self,
        stage: Literal["production", "staging"] = "production"
    ) -> tuple[any, ModelMetadata]:
        """Load model with metadata"""
        stage_path = self.base_path / stage
        
        # Load metadata
        metadata_path = stage_path / "metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"No model found in {stage}")
        
        with open(metadata_path) as f:
            metadata_dict = json.load(f)
        
        metadata = ModelMetadata(**metadata_dict)
        
        # Load model
        model_path = stage_path / f"model_{metadata.version}.pkl"
        model = joblib.load(model_path)
        
        return model, metadata
    
    def promote_to_production(self):
        """Promote staging model to production"""
        staging_path = self.base_path / "staging"
        production_path = self.base_path / "production"
        archive_path = self.base_path / "archive"
        
        # Archive current production model
        if (production_path / "metadata.json").exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_dir = archive_path / timestamp
            archive_dir.mkdir(exist_ok=True)
            
            for file in production_path.glob("*"):
                file.rename(archive_dir / file.name)
        
        # Promote staging to production
        for file in staging_path.glob("*"):
            file.rename(production_path / file.name)
        
        print("✅ Model promoted to production")


class LightGBMPipeline:
    """
    LightGBM training and inference pipeline
    
    Features:
    - Time-series cross-validation
    - Hyperparameter tuning
    - Feature importance tracking
    - Early stopping
    """
    
    def __init__(
        self,
        feature_names: list[str],
        target_name: str = "target",
        params: dict | None = None
    ):
        self.feature_names = feature_names
        self.target_name = target_name
        
        # Default params
        self.params = params or {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "num_leaves": 31,
            "learning_rate": 0.05,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "verbose": -1,
            "seed": 42
        }
        
        self.model: lgb.Booster | None = None
        self.feature_importance: pd.DataFrame | None = None
    
    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_splits: int = 5,
        early_stopping_rounds: int = 50
    ) -> dict:
        """
        Train model with time-series cross-validation
        
        Returns:
            Training metrics
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        cv_scores = []
        models = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            model = lgb.train(
                self.params,
                train_data,
                num_boost_round=1000,
                valid_sets=[val_data],
                callbacks=[
                    lgb.early_stopping(early_stopping_rounds),
                    lgb.log_evaluation(period=100)
                ]
            )
            
            # Evaluate
            y_pred = model.predict(X_val)
            y_pred_binary = (y_pred > 0.5).astype(int)
            
            fold_metrics = {
                "auc": roc_auc_score(y_val, y_pred),
                "accuracy": accuracy_score(y_val, y_pred_binary),
                "precision": precision_score(y_val, y_pred_binary),
                "recall": recall_score(y_val, y_pred_binary),
                "f1": f1_score(y_val, y_pred_binary)
            }
            
            cv_scores.append(fold_metrics)
            models.append(model)
            
            print(f"Fold {fold + 1}: AUC={fold_metrics['auc']:.4f}, "
                  f"Acc={fold_metrics['accuracy']:.4f}")
        
        # Use best model (highest AUC)
        best_idx = np.argmax([s["auc"] for s in cv_scores])
        self.model = models[best_idx]
        
        # Calculate feature importance
        importance = self.model.feature_importance(importance_type="gain")
        self.feature_importance = pd.DataFrame({
            "feature": self.feature_names,
            "importance": importance
        }).sort_values("importance", ascending=False)
        
        # Average metrics
        avg_metrics = {
            metric: np.mean([s[metric] for s in cv_scores])
            for metric in cv_scores[0].keys()
        }
        
        return avg_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict probabilities"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        return self.model.predict(X)
    
    def predict_single(self, features: np.ndarray) -> float:
        """Predict single sample (for real-time inference)"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        return self.model.predict(features.reshape(1, -1))[0]
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance"""
        if self.feature_importance is None:
            raise ValueError("Model not trained")
        
        return self.feature_importance


class ModelInference:
    """
    Fast model inference for production
    
    Features:
    - Model caching
    - Batch prediction
    - Latency tracking
    """
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.model: any | None = None
        self.metadata: ModelMetadata | None = None
        self._load_production_model()
    
    def _load_production_model(self):
        """Load production model"""
        try:
            self.model, self.metadata = self.registry.load_model("production")
            print(f"✅ Loaded model: {self.metadata.version}")
        except FileNotFoundError:
            print("⚠️ No production model found")
    
    def reload_model(self):
        """Reload model (for hot-swapping)"""
        self._load_production_model()
    
    def predict(
        self,
        features: np.ndarray | pd.DataFrame
    ) -> np.ndarray:
        """
        Predict probabilities
        
        Args:
            features: Feature array or DataFrame
            
        Returns:
            Probability array
        """
        if self.model is None:
            raise ValueError("No model loaded")
        
        if isinstance(features, pd.DataFrame):
            features = features[self.metadata.features].values
        
        return self.model.predict(features)
    
    def predict_single(self, features: np.ndarray) -> float:
        """Fast single prediction"""
        if self.model is None:
            raise ValueError("No model loaded")
        
        return self.model.predict(features.reshape(1, -1))[0]
    
    def get_model_info(self) -> dict:
        """Get model information"""
        if self.metadata is None:
            return {"error": "No model loaded"}
        
        return {
            "version": self.metadata.version,
            "type": self.metadata.model_type,
            "created_at": self.metadata.created_at,
            "features": self.metadata.features,
            "metrics": self.metadata.metrics,
            "training_samples": self.metadata.training_samples
        }


# Training script
def train_signal_model(
    data_path: str,
    output_version: str = "1.0.0"
):
    """
    Train signal prediction model
    
    Args:
        data_path: Path to training data (parquet/csv)
        output_version: Model version
    """
    print("🚀 Starting model training...")
    
    # Load data
    df = pd.read_parquet(data_path)
    print(f"📊 Loaded {len(df)} samples")
    
    # Define features
    feature_cols = [
        "vwap_dev", "zscore", "atr", "rsi",
        "vol_ratio", "vol_imbalance",
        "spread_bps", "ofi",
        "regime", "volatility_regime"
    ]
    
    X = df[feature_cols]
    y = df["target"]  # 1 = profitable signal, 0 = unprofitable
    
    # Train
    pipeline = LightGBMPipeline(feature_cols)
    metrics = pipeline.train(X, y)
    
    print("\n📈 Training Results:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    # Feature importance
    print("\n🔍 Top 10 Features:")
    print(pipeline.get_feature_importance().head(10))
    
    # Save to registry
    registry = ModelRegistry()
    metadata = ModelMetadata(
        model_id=f"signal_model_{output_version}",
        model_type="lightgbm",
        version=output_version,
        created_at=datetime.now().isoformat(),
        features=feature_cols,
        target="target",
        metrics=metrics,
        hyperparams=pipeline.params,
        training_samples=len(df)
    )
    
    registry.save_model(pipeline.model, metadata, stage="staging")
    
    print(f"\n✅ Model saved to staging: v{output_version}")
    print("Run promote_to_production() to deploy")


if __name__ == "__main__":
    # Example: Train model
    # train_signal_model("backend/data/training/signals.parquet", "1.0.0")
    
    # Example: Load and infer
    registry = ModelRegistry()
    inference = ModelInference(registry)
    
    # Test prediction
    test_features = np.array([
        5.2,   # vwap_dev
        0.8,   # zscore
        150.5, # atr
        62.3,  # rsi
        1.2,   # vol_ratio
        0.15,  # vol_imbalance
        2.5,   # spread_bps
        0.3,   # ofi
        1.0,   # regime
        1.0    # volatility_regime
    ])
    
    try:
        prob = inference.predict_single(test_features)
        print(f"🎯 Signal probability: {prob:.4f}")
    except ValueError as e:
        print(f"⚠️ {e}")


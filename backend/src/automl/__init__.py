"""
AutoML package for nightly model retraining.

Epic-5: Nightly AutoML
- Data collection (24h OHLCV)
- Feature engineering
- Hyperparameter tuning (Optuna)
- Model versioning & deployment
"""

__all__ = [
    "collect_data",
    "build_features",
    "train_lgbm",
    "train_tft",
    "evaluate",
    "versioning",
    "nightly_retrain",
]


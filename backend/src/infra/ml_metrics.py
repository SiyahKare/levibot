"""
ML-specific Prometheus metrics
"""

from prometheus_client import Counter, Gauge, Histogram

from .metrics import registry

# Feature staleness
ml_feature_staleness_seconds = Gauge(
    "ml_feature_staleness_seconds",
    "Age of latest feature row in seconds",
    ["symbol"],
    registry=registry,
)

# Model calibration / performance
ml_model_ece = Gauge(
    "ml_model_ece",
    "Expected Calibration Error of the model",
    registry=registry,
)

ml_model_auc = Gauge(
    "ml_model_auc",
    "Area Under Curve of the model",
    registry=registry,
)

ml_model_max_dd = Gauge(
    "ml_model_max_dd",
    "Max drawdown of the model policy",
    registry=registry,
)

ml_model_sharpe = Gauge(
    "ml_model_sharpe",
    "Sharpe ratio of the model policy",
    registry=registry,
)

# Prediction metrics
ml_predictions_total = Counter(
    "ml_predictions_total",
    "Total number of ML predictions made",
    ["symbol", "confidence_bucket"],
    registry=registry,
)

ml_prediction_confidence = Histogram(
    "ml_prediction_confidence",
    "Distribution of prediction confidence",
    ["symbol"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    registry=registry,
)

# Uncertainty metrics
ml_uncertainty = Gauge(
    "ml_uncertainty",
    "Model uncertainty (entropy or variance)",
    ["symbol"],
    registry=registry,
)

# Cross-asset features
ml_cross_asset_ratio = Gauge(
    "ml_cross_asset_ratio",
    "Cross-asset correlation ratio",
    ["asset1", "asset2"],
    registry=registry,
)

# Regime detection
ml_regime_state = Gauge(
    "ml_regime_state",
    "Current market regime (0=low, 1=medium, 2=high)",
    ["type"],  # type: trend, volatility, etc.
    registry=registry,
)

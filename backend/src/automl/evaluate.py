"""
Model evaluation module.

Loads trained models and extracts performance metrics.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_score(model_path: str) -> float:
    """
    Load model score from saved model file.

    Args:
        model_path: Path to model file (pkl/pt/json)

    Returns:
        Model score (accuracy/Sharpe/etc.)
    """
    try:
        path = Path(model_path)

        if not path.exists():
            print(f"[WARN] Model not found: {model_path}")
            return 0.0

        # Mock: read JSON metadata
        meta = json.loads(path.read_text())
        score = float(meta.get("score", 0.0))

        return score

    except Exception as e:
        print(f"[ERROR] Failed to load score from {model_path}: {e}")
        return 0.0


def calculate_sharpe(returns: list[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio from return series.

    TODO: Implement for backtesting results.

    Args:
        returns: List of period returns
        risk_free_rate: Risk-free rate (annualized)

    Returns:
        Sharpe ratio
    """
    if not returns or len(returns) < 2:
        return 0.0

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / len(returns)
    std_dev = variance**0.5

    if std_dev == 0:
        return 0.0

    # Annualized Sharpe (assuming daily returns)
    sharpe = (mean_return - risk_free_rate) / std_dev * (252**0.5)

    return sharpe


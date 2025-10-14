"""
Feature engineering module for AutoML pipeline.

Builds ML features from raw OHLCV data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _sma(vals: list[float], n: int) -> list[float]:
    """Calculate Simple Moving Average."""
    out = []
    s = 0.0

    for i, x in enumerate(vals):
        s += x
        if i >= n:
            s -= vals[i - n]
        out.append(s / max(1, i + 1 if i < n else n))

    return out


def _ema(vals: list[float], n: int) -> list[float]:
    """Calculate Exponential Moving Average."""
    alpha = 2.0 / (n + 1)
    out = []
    ema = vals[0] if vals else 0.0

    for x in vals:
        ema = alpha * x + (1 - alpha) * ema
        out.append(ema)

    return out


def build_features(raw_path: str, horizon: int = 5) -> dict[str, Any]:
    """
    Build ML features from raw OHLCV data.

    Features:
    - price returns (1-period, 5-period)
    - SMA gaps (20, 50)
    - EMA gaps (12, 26)
    - volume
    - volatility (rolling std)

    Target:
    - Binary classification: price up/down after N periods

    Args:
        raw_path: Path to raw OHLCV JSON file
        horizon: Future periods to look ahead for target label

    Returns:
        Dict with 'X' (features) and 'y' (labels)
    """
    rows = json.loads(Path(raw_path).read_text())

    # Extract price/volume series
    closes = [r["close"] for r in rows]
    volumes = [r["volume"] for r in rows]

    # Technical indicators
    sma20 = _sma(closes, 20)
    sma50 = _sma(closes, 50)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)

    # Build feature rows
    features = []
    labels = []

    for i in range(len(rows)):
        # Returns
        ret1 = 0.0 if i == 0 else (closes[i] - closes[i - 1]) / max(1e-9, closes[i - 1])
        ret5 = 0.0 if i < 5 else (closes[i] - closes[i - 5]) / max(1e-9, closes[i - 5])

        # Volatility (rolling std over 20 periods)
        if i >= 20:
            recent = closes[i - 20 : i + 1]
            mean = sum(recent) / len(recent)
            var = sum((x - mean) ** 2 for x in recent) / len(recent)
            vol = var**0.5
        else:
            vol = 0.0

        f = {
            "close": closes[i],
            "ret1": ret1,
            "ret5": ret5,
            "sma20_gap": closes[i] - sma20[i],
            "sma50_gap": closes[i] - sma50[i],
            "ema12_gap": closes[i] - ema12[i],
            "ema26_gap": closes[i] - ema26[i],
            "volume": volumes[i],
            "volatility": vol,
        }
        features.append(f)

        # Target: price direction after 'horizon' periods
        j = min(len(closes) - 1, i + horizon)
        label = 1 if closes[j] > closes[i] else 0
        labels.append(label)

    return {"X": features, "y": labels}

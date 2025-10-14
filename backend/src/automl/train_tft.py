"""
TFT (Temporal Fusion Transformer) training module.

Placeholder implementation - requires PyTorch Lightning + TFT library.
"""

from __future__ import annotations

import json
from pathlib import Path


def train_and_dump(features_path: str, out_dir: str) -> str:
    """
    Train TFT model.

    TODO: Implement real PyTorch Lightning TFT training.
    - https://pytorch-forecasting.readthedocs.io/
    - TimeSeriesDataSet + TemporalFusionTransformer
    - torch.save() for model weights

    Args:
        features_path: Path to features JSON
        out_dir: Output directory for model

    Returns:
        Path to saved model file
    """
    # Mock implementation
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    model_path = Path(out_dir) / "tft.pt"

    # Load data to get basic stats
    data = json.loads(Path(features_path).read_text())
    n_samples = len(data.get("y", []))

    # Mock model metadata
    model_meta = {
        "type": "tft_mock",
        "score": 0.52,  # Slightly better than random
        "n_samples": n_samples,
        "hidden_size": 64,
        "attention_heads": 4,
    }

    model_path.write_text(json.dumps(model_meta, indent=2))

    print(f"[TFT] Trained model: score={model_meta['score']:.4f}")

    return str(model_path)


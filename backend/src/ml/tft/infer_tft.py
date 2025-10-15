"""Thread-safe TFT inference wrapper."""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
import torch


class TFTProd:
    """Thread-safe singleton wrapper for production TFT inference."""

    _lock = threading.Lock()
    _ckpt_meta = None

    @classmethod
    def load(cls, path: str = "backend/data/models/best_tft.pt"):
        """
        Load TFT checkpoint metadata (thread-safe).

        Args:
            path: Path to TFT export file (relative to project root or absolute)

        Returns:
            Checkpoint metadata dictionary
        """
        with cls._lock:
            if cls._ckpt_meta is None:
                # Resolve path: try relative to /app (Docker) or as-is
                resolved_path = Path(path)
                if not resolved_path.exists():
                    # Try relative to /app in Docker
                    resolved_path = Path(f"/app/{path}")
                if not resolved_path.exists():
                    # Try data/models (relative to /app)
                    resolved_path = Path("data/models") / Path(path).name
                
                cls._ckpt_meta = torch.load(str(resolved_path), weights_only=False)
        return cls._ckpt_meta

    @classmethod
    def predict_proba_up(cls, seq_window: np.ndarray) -> float:
        """
        Predict probability of upward price movement.

        Args:
            seq_window: Sequence window array (L, F)

        Returns:
            Probability (0.0 - 1.0) of upward movement

        Note:
            Placeholder implementation. Real implementation would:
            - Load model from checkpoint: LightningModule.load_from_checkpoint(cls._ckpt_meta["best_ckpt"])
            - Run forward pass: model(torch.from_numpy(seq_window).unsqueeze(0))
        """
        cls.load()

        # Simple heuristic: trend from first to last close
        diff = float(seq_window[-1][0] - seq_window[0][0])
        return float(0.5 + max(min(diff, 1.0), -1.0) * 0.01)


"""Thread-safe TFT inference wrapper."""

from __future__ import annotations

import threading

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
            path: Path to TFT export file

        Returns:
            Checkpoint metadata dictionary
        """
        with cls._lock:
            if cls._ckpt_meta is None:
                cls._ckpt_meta = torch.load(path)
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


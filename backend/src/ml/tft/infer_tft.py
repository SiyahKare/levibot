"""Thread-safe TFT inference wrapper with warm-up pool."""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


# Import SimpleTFT architecture (same as training)
# For production, this would be imported from train_tft_prod
class SimpleTFT(nn.Module):
    """Simplified TFT architecture."""

    def __init__(
        self,
        input_size: int,
        seq_len: int,
        hidden_size: int = 128,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.seq_len = seq_len
        self.hidden_size = hidden_size

        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers=2,
            dropout=dropout,
            batch_first=True,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        proba = self.fc(last_hidden)
        return proba


class TFTProd:
    """Thread-safe singleton wrapper for production TFT inference."""

    _lock = threading.Lock()
    _model: nn.Module | None = None
    _seq_len: int = 64
    _n_features: int = 5

    @classmethod
    def load(cls, path: str = "backend/data/models/best_tft.pt"):
        """
        Load TFT model (thread-safe).

        Args:
            path: Path to TFT model file (relative to project root or absolute)

        Returns:
            Loaded model
        """
        with cls._lock:
            if cls._model is None:
                # Resolve path: try relative to /app (Docker) or as-is
                resolved_path = Path(path)
                if not resolved_path.exists():
                    # Try relative to /app in Docker
                    resolved_path = Path(f"/app/{path}")
                if not resolved_path.exists():
                    # Try data/models (relative to /app)
                    resolved_path = Path("data/models") / Path(path).name

                print(f"🔧 Loading TFT model from: {resolved_path}")

                # Load model
                cls._model = SimpleTFT(
                    input_size=cls._n_features,
                    seq_len=cls._seq_len,
                    hidden_size=128,
                    dropout=0.1,
                )

                # Load weights
                state_dict = torch.load(str(resolved_path), weights_only=True)
                cls._model.load_state_dict(state_dict)
                cls._model.eval()

                # Set single thread for consistent latency
                torch.set_num_threads(1)

                # Warm-up (precompile JIT, cache)
                warmup_input = torch.randn(1, cls._seq_len, cls._n_features)
                for _ in range(10):
                    with torch.no_grad():
                        _ = cls._model(warmup_input)

                print("✅ TFT model loaded and warmed up!")

        return cls._model

    @classmethod
    def predict_proba_up(cls, seq_window: np.ndarray) -> float:
        """
        Predict probability of upward price movement.

        Args:
            seq_window: Sequence window array (seq_len, n_features)

        Returns:
            Probability (0.0 - 1.0) of upward movement
        """
        model = cls.load()

        # Convert to tensor
        x = torch.from_numpy(seq_window).float().unsqueeze(0)  # (1, seq_len, n_features)

        # Inference
        with torch.no_grad():
            proba = model(x).squeeze().item()

        return float(proba)


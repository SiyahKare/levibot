"""TinyTFT: Lightweight LSTM-based model for binary time-series prediction."""

from __future__ import annotations

import pytorch_lightning as pl
import torch
import torch.nn as nn


class TinyTFT(pl.LightningModule):
    """Simple and fast: LSTM backbone + sigmoid head (placeholder for full TFT)."""

    def __init__(
        self,
        in_features: int,
        hidden: int = 64,
        lr: float = 1e-3,
        pos_weight: float | None = None,
    ):
        """
        Initialize TinyTFT model.

        Args:
            in_features: Number of input features
            hidden: LSTM hidden size
            lr: Learning rate
            pos_weight: Positive class weight for imbalanced data
        """
        super().__init__()
        self.save_hyperparameters()

        self.lstm = nn.LSTM(
            input_size=in_features, hidden_size=hidden, batch_first=True
        )
        self.head = nn.Sequential(nn.Linear(hidden, 1), nn.Sigmoid())
        self.loss = nn.BCELoss()

    def forward(self, x):
        """
        Forward pass.

        Args:
            x: Input tensor (B, L, F)

        Returns:
            Prediction tensor (B,)
        """
        y, (h, _) = self.lstm(x)
        out = self.head(h[-1])  # (B, 1)
        return out.squeeze(-1)  # (B,)

    def training_step(self, batch, batch_idx):
        x, y = batch
        yhat = self(x)
        loss = self.loss(yhat, y)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        yhat = self(x)
        loss = self.loss(yhat, y)
        acc = ((yhat > 0.5).float() == y).float().mean()
        self.log_dict({"val_loss": loss, "val_acc": acc}, prog_bar=True)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)


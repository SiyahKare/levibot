"""Production TFT training with PyTorch Lightning."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytorch_lightning as pl
import torch
from torch.utils.data import DataLoader

from .dataset import SeqDataset
from .model import TinyTFT

FEATURES = ["close", "ret1", "sma20_gap", "sma50_gap", "vol_z"]


def _time_split(df: pd.DataFrame, val_days: int = 14):
    """Split DataFrame by time."""
    ts = pd.to_datetime(df["ts"], unit="ms", utc=True)
    cutoff = ts.max() - pd.Timedelta(days=val_days)
    return df.loc[ts <= cutoff], df.loc[ts > cutoff]


def train_from_parquet(
    parquet_path: str,
    lookback: int = 60,
    horizon: int = 5,
    val_days: int = 14,
    max_epochs: int = 30,
    patience: int = 5,
):
    """
    Train TFT model from Parquet feature store.

    Args:
        parquet_path: Path to feature store Parquet file
        lookback: Window size for sequence
        horizon: Steps ahead for prediction
        val_days: Days for validation set
        max_epochs: Maximum training epochs
        patience: Early stopping patience

    Returns:
        Dictionary with paths to artifacts
    """
    df = pd.read_parquet(parquet_path)
    tr, va = _time_split(df, val_days)

    ds_tr = SeqDataset(tr, FEATURES, "y", lookback, horizon)
    ds_va = SeqDataset(va, FEATURES, "y", lookback, horizon)

    dl_tr = DataLoader(ds_tr, batch_size=256, shuffle=True, num_workers=0)
    dl_va = DataLoader(ds_va, batch_size=512, shuffle=False, num_workers=0)

    model = TinyTFT(in_features=len(FEATURES))
    out_dir = Path("backend/data/models") / datetime.now(UTC).strftime(
        "%Y-%m-%d"
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    ckpt_cb = pl.callbacks.ModelCheckpoint(
        monitor="val_acc", mode="max", dirpath=str(out_dir), filename="tft"
    )
    es_cb = pl.callbacks.EarlyStopping(monitor="val_acc", mode="max", patience=patience)

    trainer = pl.Trainer(
        max_epochs=max_epochs,
        accelerator="auto",
        devices=1,
        log_every_n_steps=10,
        callbacks=[ckpt_cb, es_cb],
        enable_checkpointing=True,
    )
    trainer.fit(model, dl_tr, dl_va)

    best_ckpt = ckpt_cb.best_model_path

    # Lightweight export: save checkpoint path
    best_pt = out_dir / "tft.pt"
    torch.save({"best_ckpt": best_ckpt}, best_pt)

    card = {
        "model": "TinyTFT",
        "features": FEATURES,
        "lookback": lookback,
        "horizon": horizon,
        "val_days": val_days,
        "best_ckpt": best_ckpt,
        "created_at": datetime.now(UTC).isoformat(),
    }
    (out_dir / "model_card_tft.json").write_text(json.dumps(card, indent=2))

    # Symlink for production
    best_link = Path("backend/data/models/best_tft.pt")
    if best_link.exists() or best_link.is_symlink():
        best_link.unlink()
    best_link.symlink_to(best_pt.resolve())

    return {"best_pt": str(best_pt), "card": str(out_dir / "model_card_tft.json")}


#!/usr/bin/env python3
"""
Train Deep Transformer Model

Trains a Transformer-based sequence model for multi-asset prediction.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.models.deep_tfm import SeqTransformer

# Model hyperparameters
SEQ_LEN = 128
FEATURES = [
    "ret_1",
    "ema_20",
    "ema_50",
    "ema_200",
    "z_20",
    "range",
    "vol_20",
    "ratio_BTC_ETH",
    "ratio_ETH_SOL",
    "lead_ret_BTC",
]


class CryptoSequenceDataset(Dataset):
    """Dataset for sequence-based crypto prediction."""
    
    def __init__(self, df: pl.DataFrame, symbol: str, seq_len: int = 128):
        self.seq_len = seq_len
        
        # Filter and sort
        df = df.filter(pl.col("symbol") == symbol).sort("timestamp")
        
        # Extract features
        self.X = df.select(FEATURES).fill_null(0).to_numpy().astype(np.float32)
        
        # Labels
        self.y_cls = df["label_direction"].to_numpy().astype(np.float32)
        self.y_reg = df["label_return"].fill_null(0).to_numpy().astype(np.float32)
    
    def __len__(self) -> int:
        return max(0, len(self.X) - self.seq_len - 1)
    
    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        # Sequence
        x = self.X[idx : idx + self.seq_len]
        
        # Target (at end of sequence)
        y_cls = self.y_cls[idx + self.seq_len]
        y_reg = self.y_reg[idx + self.seq_len]
        
        return (
            torch.tensor(x, dtype=torch.float32),
            torch.tensor(y_cls, dtype=torch.float32),
            torch.tensor(y_reg, dtype=torch.float32),
        )


def train_model(
    symbol: str = "BTCUSDT",
    data_path: str = "backend/data/feature_multi/fe_multi_15m.parquet",
    output_dir: str = "backend/models",
    epochs: int = 30,
    batch_size: int = 64,
    lr: float = 2e-4,
):
    """Train the deep transformer model."""
    print(f"\n{'='*70}")
    print("🧠 DEEP TRANSFORMER TRAINING")
    print(f"{'='*70}\n")
    
    print(f"Symbol: {symbol}")
    print(f"Sequence length: {SEQ_LEN}")
    print(f"Features: {len(FEATURES)}")
    
    # Load data
    print(f"\nLoading data from {data_path}...")
    if not Path(data_path).exists():
        print(f"❌ Data file not found: {data_path}")
        print("   Run: python backend/ml/feature_store/ingest_multi.py")
        sys.exit(1)
    
    df = pl.read_parquet(data_path)
    
    # Create dataset
    print("Creating datasets...")
    dataset = CryptoSequenceDataset(df, symbol, seq_len=SEQ_LEN)
    
    if len(dataset) == 0:
        print(f"❌ No data for {symbol}")
        sys.exit(1)
    
    print(f"  Total samples: {len(dataset)}")
    
    # Train/validation split (80/20)
    n_train = int(len(dataset) * 0.8)
    n_val = len(dataset) - n_train
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [n_train, n_val], generator=torch.Generator().manual_seed(42)
    )
    
    print(f"  Train: {len(train_dataset)}, Val: {len(val_dataset)}")
    
    # Data loaders
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True, num_workers=0
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False, num_workers=0
    )
    
    # Model
    print("\nInitializing model...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"  Device: {device}")
    
    model = SeqTransformer(in_dim=len(FEATURES)).to(device)
    
    # Count parameters
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  Parameters: {n_params:,}")
    
    # Optimizer
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    
    # Loss functions
    bce_loss = nn.BCEWithLogitsLoss()
    mse_loss = nn.MSELoss()
    
    # Training loop
    print(f"\n{'─'*70}")
    print("TRAINING")
    print(f"{'─'*70}\n")
    
    best_val_acc = 0.0
    best_epoch = 0
    
    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        
        for x, y_cls, y_reg in train_loader:
            x, y_cls, y_reg = x.to(device), y_cls.to(device), y_reg.to(device)
            
            optimizer.zero_grad()
            
            logit, mu, sigma = model(x)
            
            # Combined loss
            loss_cls = bce_loss(logit, y_cls)
            loss_reg = mse_loss(mu, y_reg)
            loss_unc = sigma.mean()  # Regularize uncertainty
            
            loss = loss_cls + 0.1 * loss_reg + 0.01 * loss_unc
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for x, y_cls, y_reg in val_loader:
                x, y_cls = x.to(device), y_cls.to(device)
                
                logit, _, _ = model(x)
                pred = (torch.sigmoid(logit) > 0.5).float()
                
                val_correct += (pred == y_cls).sum().item()
                val_total += len(y_cls)
        
        val_acc = val_correct / val_total if val_total > 0 else 0.0
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch
            
            # Save checkpoint
            output_path = Path(output_dir) / f"deep_tfm_{symbol}_{epoch}.pt"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_acc": val_acc,
                    "features": FEATURES,
                    "seq_len": SEQ_LEN,
                },
                output_path,
            )
        
        # Print progress
        print(
            f"Epoch {epoch:2d} | "
            f"Loss: {train_loss:.4f} | "
            f"Val Acc: {val_acc:.3f} | "
            f"Best: {best_val_acc:.3f} @ {best_epoch}"
        )
    
    # Final save
    final_path = Path(output_dir) / f"deep_tfm_{symbol}_final.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "features": FEATURES,
            "seq_len": SEQ_LEN,
            "best_val_acc": best_val_acc,
            "best_epoch": best_epoch,
        },
        final_path,
    )
    
    print(f"\n{'─'*70}")
    print("✅ TRAINING COMPLETE!")
    print(f"{'─'*70}\n")
    print(f"  Best val acc: {best_val_acc:.3f} @ epoch {best_epoch}")
    print(f"  Saved: {final_path}")
    
    # Update registry
    registry_path = Path("backend/data/registry/model_registry.json")
    if registry_path.exists():
        with open(registry_path) as f:
            registry = json.load(f)
    else:
        registry = {}
    
    if "deep" not in registry:
        registry["deep"] = {}
    
    registry["deep"][symbol] = {
        "path": str(final_path),
        "features": FEATURES,
        "seq_len": SEQ_LEN,
        "best_val_acc": float(best_val_acc),
        "best_epoch": best_epoch,
        "symbol": symbol,
    }
    
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    print(f"  Registry updated: {registry_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Train deep transformer model")
    parser.add_argument("--symbol", default="BTCUSDT", help="Symbol to train on")
    parser.add_argument(
        "--data",
        default="backend/data/feature_multi/fe_multi_15m.parquet",
        help="Data file path",
    )
    parser.add_argument("--epochs", type=int, default=30, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=2e-4, help="Learning rate")
    
    args = parser.parse_args()
    
    train_model(
        symbol=args.symbol,
        data_path=args.data,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )


if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Simple Model Training Script
Trains a basic LogisticRegression model for up/down prediction
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split


def generate_dummy_training_data(n_samples=1000):
    """
    Generate synthetic training data.
    
    In production, replace this with:
    - Load trades history from TimescaleDB
    - Fetch market_ticks data
    - Compute features using backend.src.ai.features
    - Label: 1 if price went up in next 60s, 0 otherwise
    """
    print(f"🔧 Generating {n_samples} synthetic training samples...")
    
    # Feature vector: [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60]
    X = np.random.randn(n_samples, 6)
    
    # Synthetic labels: positive returns → 1 (up), negative → 0 (down)
    # Simple rule: if sum of features > 0 → up
    y = (X.sum(axis=1) > 0).astype(int)
    
    return X, y


def train_model(X, y):
    """Train logistic regression model."""
    print("🤖 Training LogisticRegression model...")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    clf = LogisticRegression(max_iter=200, random_state=42)
    clf.fit(X_train, y_train)
    
    train_acc = clf.score(X_train, y_train)
    test_acc = clf.score(X_test, y_test)
    
    print(f"  ✅ Train accuracy: {train_acc:.3f}")
    print(f"  ✅ Test accuracy:  {test_acc:.3f}")
    
    return clf


def save_model(clf, path="ops/models/model.skops"):
    """Save model to disk."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, path)
    print(f"💾 Model saved to: {path}")


def main():
    print("=" * 50)
    print("LEVIBOT - Simple Model Training")
    print("=" * 50)
    print("")
    
    # Generate training data
    X, y = generate_dummy_training_data(n_samples=1000)
    
    # Train model
    clf = train_model(X, y)
    
    # Save model
    output_path = os.getenv("MODEL_OUTPUT", "ops/models/model.skops")
    save_model(clf, output_path)
    
    print("")
    print("=" * 50)
    print("✅ Training complete!")
    print("=" * 50)
    print("")
    print("Next steps:")
    print("  1. Restart backend to load new model")
    print("  2. Select 'skops-local' in panel Model Selector")
    print("  3. Test: curl 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s'")
    print("")
    print("⚠️  NOTE: This uses synthetic data. For production:")
    print("   - Load real trades from TimescaleDB")
    print("   - Compute actual features (ret, vol, rsi, etc.)")
    print("   - Label based on actual price movements")
    print("")


if __name__ == "__main__":
    main()


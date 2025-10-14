#!/usr/bin/env python3
"""
Production Model Training Script
Trains model using real trades and market data from TimescaleDB
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import joblib
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from backend.src.infra.settings import settings


def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
    )


def fetch_training_data(symbol: str = "BTCUSDT", days: int = 28):
    """
    Fetch training data from TimescaleDB.
    
    Args:
        symbol: Trading pair
        days: Number of days to fetch
    
    Returns:
        List of (timestamp, features, label) tuples
    """
    print(f"📊 Fetching {days} days of data for {symbol}...")
    
    conn = get_db_connection()
    samples = []
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Fetch historical 1s candles (or raw ticks if m1s doesn't exist)
            try:
                # Try continuous aggregate first
                cur.execute(
                    """
                    SELECT t AS ts, close AS price
                    FROM m1s
                    WHERE symbol = %s
                      AND t > NOW() - INTERVAL '%s days'
                    ORDER BY t ASC
                    """,
                    (symbol, days)
                )
            except psycopg2.errors.UndefinedTable:
                # Fallback to raw ticks
                cur.execute(
                    """
                    SELECT ts, last AS price
                    FROM market_ticks
                    WHERE symbol = %s
                      AND ts > NOW() - INTERVAL '%s days'
                    ORDER BY ts ASC
                    """,
                    (symbol, days)
                )
            
            rows = cur.fetchall()
    
    finally:
        conn.close()
    
    if len(rows) < 400:
        print(f"⚠️  Insufficient data: {len(rows)} rows (need 400+)")
        return []
    
    print(f"✅ Fetched {len(rows):,} rows")
    
    # Convert to numpy
    timestamps = np.array([r["ts"] for r in rows])
    prices = np.array([float(r["price"]) for r in rows], dtype=np.float64)
    
    # Generate samples with sliding window
    print("🔧 Computing features and labels...")
    
    window = 300  # 5 minutes of 1s data
    horizon = 60  # 60s ahead label
    
    for i in range(window, len(prices) - horizon):
        # Features: last 300s of price data
        price_window = prices[i - window:i]
        
        # Compute features (same as features_v2.py)
        features = _compute_features(price_window)
        
        # Label: price went up in next 60s?
        future_price = prices[i + horizon]
        current_price = prices[i]
        label = 1 if future_price > current_price else 0
        
        samples.append({
            "ts": timestamps[i],
            "features": features,
            "label": label,
            "current_price": current_price,
            "future_price": future_price
        })
    
    print(f"✅ Generated {len(samples):,} training samples")
    
    return samples


def _compute_features(prices: np.ndarray) -> list[float]:
    """
    Compute features from price window.
    
    Returns:
        [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60]
    """
    n = len(prices)
    
    # Returns
    ret_1m = (prices[-1] - prices[-60]) / (prices[-60] + 1e-9) if n >= 60 else 0.0
    ret_5m = (prices[-1] - prices[-300]) / (prices[-300] + 1e-9) if n >= 300 else 0.0
    
    # Volatility
    vol_1m = np.std(prices[-60:]) / (np.mean(prices[-60:]) + 1e-9) if n >= 60 else 0.0
    vol_5m = np.std(prices[-300:]) / (np.mean(prices[-300:]) + 1e-9) if n >= 300 else 0.0
    
    # RSI
    rsi_14 = _rsi(prices, 14) if n >= 15 else 50.0
    
    # Z-score
    zscore_60 = _zscore(prices, 60) if n >= 60 else 0.0
    
    return [ret_1m, ret_5m, vol_1m, vol_5m, rsi_14, zscore_60]


def _rsi(arr: np.ndarray, period: int = 14) -> float:
    """RSI indicator."""
    if len(arr) < period + 1:
        return 50.0
    
    deltas = np.diff(arr[-period - 1:])
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return float(np.clip(rsi, 0, 100))


def _zscore(arr: np.ndarray, period: int = 60) -> float:
    """Z-score of last value vs. recent window."""
    if len(arr) < period:
        return 0.0
    
    window = arr[-period:]
    mean = np.mean(window)
    std = np.std(window)
    
    if std == 0:
        return 0.0
    
    return float((arr[-1] - mean) / std)


def train_model(samples: list[dict], model_type: str = "lr"):
    """
    Train model on samples.
    
    Args:
        samples: Training samples from fetch_training_data()
        model_type: "lr" (LogisticRegression) or "gb" (GradientBoosting)
    
    Returns:
        Trained model
    """
    print(f"🤖 Training {model_type.upper()} model...")
    
    # Extract X, y
    X = np.array([s["features"] for s in samples])
    y = np.array([s["label"] for s in samples])
    
    # Train/test split (last 7 days = test)
    test_size = min(0.2, 7 * 86400 / len(samples))  # ~7 days or 20%
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False, random_state=42
    )
    
    print(f"  Train samples: {len(X_train):,}")
    print(f"  Test samples:  {len(X_test):,}")
    print(f"  Positive rate: {y.mean():.3f}")
    
    # Train
    if model_type == "gb":
        clf = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            random_state=42
        )
    else:
        clf = LogisticRegression(max_iter=200, random_state=42)
    
    clf.fit(X_train, y_train)
    
    # Evaluate
    train_acc = clf.score(X_train, y_train)
    test_acc = clf.score(X_test, y_test)
    
    print(f"  ✅ Train accuracy: {train_acc:.3f}")
    print(f"  ✅ Test accuracy:  {test_acc:.3f}")
    
    return clf, {"train_acc": train_acc, "test_acc": test_acc}


def save_model_with_metadata(clf, metrics: dict, symbol: str, output_dir: str = "ops/models"):
    """Save model and metadata."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = f"{output_dir}/model.skops"
    joblib.dump(clf, model_path)
    print(f"💾 Model saved to: {model_path}")
    
    # Save metadata
    meta = {
        "version": "v1.0.0",
        "trained_at": datetime.utcnow().isoformat(),
        "symbol": symbol,
        "features": ["ret_1m", "ret_5m", "vol_1m", "vol_5m", "rsi_14", "zscore_60"],
        "horizon": "60s",
        "model_type": clf.__class__.__name__,
        "metrics": metrics,
        "notes": "Production model trained on real market data"
    }
    
    meta_path = f"{output_dir}/meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"📄 Metadata saved to: {meta_path}")
    
    return model_path, meta_path


def main():
    print("=" * 60)
    print("LEVIBOT - Production Model Training")
    print("=" * 60)
    print("")
    
    # Config
    symbol = os.getenv("SYMBOL", "BTCUSDT")
    days = int(os.getenv("TRAIN_DAYS", "28"))
    model_type = os.getenv("MODEL_TYPE", "lr")  # lr or gb
    
    # Fetch data
    samples = fetch_training_data(symbol=symbol, days=days)
    
    if not samples:
        print("❌ No training data available. Exiting.")
        print("")
        print("📌 Hints:")
        print("  1. Check if market_ticks table has data:")
        print("     SELECT count(*) FROM market_ticks WHERE symbol = 'BTCUSDT';")
        print("  2. Run datafeed to populate market_ticks")
        print("  3. Or seed test data:")
        print("     INSERT INTO market_ticks(symbol, ts, last)")
        print("     SELECT 'BTCUSDT', now()-(i||'s')::interval, 50000+random()*100")
        print("     FROM generate_series(0,10000) as s(i);")
        return
    
    # Train
    clf, metrics = train_model(samples, model_type=model_type)
    
    # Save
    model_path, meta_path = save_model_with_metadata(clf, metrics, symbol)
    
    print("")
    print("=" * 60)
    print("✅ Training complete!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("  1. Restart backend:")
    print("     pkill -f uvicorn && uvicorn backend.src.app.main:app --host 0.0.0.0 --port 8000")
    print("  2. Select 'skops-local' in panel Model Selector")
    print("  3. Test prediction:")
    print("     curl 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s'")
    print("")
    print(f"📊 Model: {model_path}")
    print(f"📄 Meta:  {meta_path}")
    print("")


if __name__ == "__main__":
    main()


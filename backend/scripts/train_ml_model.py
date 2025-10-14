#!/usr/bin/env python3
"""
Train ML Model - End-to-End Pipeline

Usage:
    python backend/scripts/train_ml_model.py --symbol BTCUSDT --days 30
"""
import argparse
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ml.backtest.engine import walk_forward_backtest
from ml.feature_store import DataIngestor, FeatureEngineer, FeatureStore
from ml.models import train_baseline_model


def main():
    parser = argparse.ArgumentParser(description="Train ML prediction model")
    parser.add_argument("--symbol", default="BTCUSDT", help="Trading symbol")
    parser.add_argument("--timeframe", default="15m", help="Timeframe")
    parser.add_argument("--days", type=int, default=30, help="Days of historical data")
    parser.add_argument("--exchange", default="binance", help="Exchange ID")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip data ingestion")
    parser.add_argument("--skip-backtest", action="store_true", help="Skip backtesting")
    
    args = parser.parse_args()
    
    print(f"\n{'='*70}")
    print("🚀 ML TRAINING PIPELINE")
    print(f"{'='*70}\n")
    
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Data Days: {args.days}")
    print(f"Exchange: {args.exchange}\n")
    
    # 1. Data Ingestion
    if not args.skip_ingest:
        print(f"\n{'─'*70}")
        print("📥 STEP 1: DATA INGESTION")
        print(f"{'─'*70}\n")
        
        ingestor = DataIngestor(exchange_id=args.exchange)
        df = ingestor.fetch_historical(
            symbol=args.symbol,
            timeframe=args.timeframe,
            days=args.days,
        )
        ingestor.close()
        
        if len(df) == 0:
            print("❌ No data fetched. Exiting.")
            return
        
        # 2. Feature Engineering
        print(f"\n{'─'*70}")
        print("🔧 STEP 2: FEATURE ENGINEERING")
        print(f"{'─'*70}\n")
        
        df = FeatureEngineer.engineer_features(df, include_labels=True)
        
        # 3. Save to Feature Store
        print(f"\n{'─'*70}")
        print("💾 STEP 3: SAVE TO FEATURE STORE")
        print(f"{'─'*70}\n")
        
        store = FeatureStore()
        store.save_features(df, symbol=args.symbol, timeframe=args.timeframe)
    
    # 4. Train Model
    print(f"\n{'─'*70}")
    print("🤖 STEP 4: TRAIN MODEL")
    print(f"{'─'*70}\n")
    
    metrics = train_baseline_model(
        symbol=args.symbol,
        timeframe=args.timeframe,
    )
    
    # 5. Backtest
    if not args.skip_backtest:
        print(f"\n{'─'*70}")
        print("📊 STEP 5: WALK-FORWARD BACKTEST")
        print(f"{'─'*70}\n")
        
        # Load features
        store = FeatureStore()
        df = store.load_features(symbol=args.symbol, timeframe=args.timeframe)
        
        if df is not None and len(df) > 0:
            # Load model
            import json
            with open("backend/data/registry/model_registry.json") as f:
                registry = json.load(f)["current"]
            
            import lightgbm as lgb
            model = lgb.Booster(model_file=registry["path"])
            
            # Run backtest
            backtest_metrics = walk_forward_backtest(
                df,
                model,
                registry["features"],
            )
            
            print(f"\n{'='*70}")
            print("🎉 TRAINING COMPLETE!")
            print(f"{'='*70}\n")
            
            print("📊 Model Metrics:")
            for k, v in metrics.items():
                print(f"  {k:20s} {v}")
            
            print("\n📈 Backtest Results:")
            for k, v in backtest_metrics.items():
                if isinstance(v, float):
                    print(f"  {k:20s} {v:.4f}")
                else:
                    print(f"  {k:20s} {v}")
        else:
            print("⚠️  No features found for backtest")
    
    print("\n✅ Pipeline complete!\n")


if __name__ == "__main__":
    main()


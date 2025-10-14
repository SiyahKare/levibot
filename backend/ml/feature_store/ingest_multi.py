#!/usr/bin/env python3
"""
Multi-Asset Data Ingestion

Fetches and processes data for multiple symbols with cross-asset features.
"""
import sys
import time
from pathlib import Path

import ccxt
import polars as pl

# Symbols to track
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
TIMEFRAME = "15m"
LIMIT = 1500  # ~15 days of 15m bars


def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str) -> pl.DataFrame:
    """Fetch OHLCV data for a symbol."""
    print(f"  Fetching {symbol}...")
    
    try:
        data = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=LIMIT)
        
        # Convert to Polars DataFrame
        df = pl.DataFrame(
            data,
            schema=["timestamp", "open", "high", "low", "close", "volume"],
        )
        
        # Add symbol column
        symbol_clean = symbol.replace("/", "")
        df = df.with_columns(pl.lit(symbol_clean).alias("symbol"))
        
        # Convert timestamp to datetime
        df = df.with_columns(
            pl.from_epoch(pl.col("timestamp"), time_unit="ms").alias("timestamp")
        )
        
        return df
    
    except Exception as e:
        print(f"  ❌ Error fetching {symbol}: {e}")
        return pl.DataFrame()


def add_basic_features(df: pl.DataFrame) -> pl.DataFrame:
    """Add basic technical indicators."""
    df = df.sort("timestamp")
    
    # Returns
    df = df.with_columns(
        (pl.col("close").log() - pl.col("close").shift(1).log()).alias("ret_1")
    )
    
    # EMAs
    df = df.with_columns([
        pl.col("close").ewm_mean(span=20, ignore_nulls=True).alias("ema_20"),
        pl.col("close").ewm_mean(span=50, ignore_nulls=True).alias("ema_50"),
        pl.col("close").ewm_mean(span=200, ignore_nulls=True).alias("ema_200"),
    ])
    
    # Z-score (20 period)
    df = df.with_columns([
        (
            (pl.col("close") - pl.col("close").rolling_mean(20))
            / (pl.col("close").rolling_std(20) + 1e-9)
        ).alias("z_20")
    ])
    
    # Range
    df = df.with_columns((pl.col("high") - pl.col("low")).alias("range"))
    
    # Volatility
    df = df.with_columns(
        pl.col("ret_1").rolling_std(20).alias("vol_20")
    )
    
    return df


def add_cross_asset_features(all_data: pl.DataFrame) -> pl.DataFrame:
    """Add cross-asset features (ratios, correlations, lead indicators)."""
    print("  Computing cross-asset features...")
    
    # Pivot to get prices side-by-side
    pivot = all_data.select(["timestamp", "symbol", "close", "ret_1"]).pivot(
        index="timestamp", columns="symbol", values=["close", "ret_1"]
    )
    
    # Compute ratios
    cross_features = pivot.select([
        pl.col("timestamp"),
        # BTC/ETH ratio
        (
            pl.col(("close", "BTCUSDT")) / pl.col(("close", "ETHUSDT"))
        ).alias("ratio_BTC_ETH"),
        # ETH/SOL ratio
        (
            pl.col(("close", "ETHUSDT")) / pl.col(("close", "SOLUSDT"))
        ).alias("ratio_ETH_SOL"),
        # BTC lead return (for other assets)
        pl.col(("ret_1", "BTCUSDT")).alias("lead_ret_BTC"),
    ])
    
    # Join back to main data
    result = all_data.join(cross_features, on="timestamp", how="left")
    
    return result


def generate_labels(df: pl.DataFrame) -> pl.DataFrame:
    """Generate prediction labels."""
    # Future return (1 bar ahead)
    df = df.with_columns(
        pl.col("ret_1").shift(-1).alias("ret_fwd_1")
    )
    
    # Direction label (1 = up, 0 = down)
    df = df.with_columns(
        (pl.col("ret_fwd_1") > 0).cast(pl.Int64).alias("label_direction")
    )
    
    # Magnitude label (for regression)
    df = df.with_columns(
        pl.col("ret_fwd_1").alias("label_return")
    )
    
    return df


def main():
    print(f"\n{'='*70}")
    print("🔄 MULTI-ASSET DATA INGESTION")
    print(f"{'='*70}\n")
    
    # Initialize exchange
    print("Initializing exchange...")
    exchange = ccxt.binance()
    exchange.load_markets()
    
    # Fetch data for all symbols
    print(f"\nFetching {len(SYMBOLS)} symbols...")
    frames = []
    
    for symbol in SYMBOLS:
        df = fetch_ohlcv(exchange, symbol)
        if len(df) > 0:
            df = add_basic_features(df)
            frames.append(df)
        
        # Rate limiting
        time.sleep(exchange.rateLimit / 1000)
    
    if not frames:
        print("\n❌ No data fetched!")
        sys.exit(1)
    
    # Concatenate all data
    print("\nMerging data...")
    all_data = pl.concat(frames)
    
    # Add cross-asset features
    all_data = add_cross_asset_features(all_data)
    
    # Generate labels
    print("  Generating labels...")
    all_data = generate_labels(all_data)
    
    # Remove rows with null labels
    all_data = all_data.filter(pl.col("label_direction").is_not_null())
    
    # Save
    output_dir = Path("backend/data/feature_multi")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "fe_multi_15m.parquet"
    all_data.write_parquet(output_file)
    
    print(f"\n✅ Saved: {output_file}")
    print(f"   Shape: {all_data.shape}")
    print(f"   Symbols: {all_data['symbol'].unique().to_list()}")
    print(f"   Date range: {all_data['timestamp'].min()} to {all_data['timestamp'].max()}")
    
    # Summary statistics
    print("\n📊 Summary by symbol:")
    summary = all_data.group_by("symbol").agg([
        pl.col("close").count().alias("bars"),
        pl.col("label_direction").mean().alias("pct_up"),
        pl.col("ret_1").std().alias("volatility"),
    ])
    print(summary)
    
    print(f"\n{'='*70}")
    print("🎉 MULTI-ASSET INGESTION COMPLETE!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()


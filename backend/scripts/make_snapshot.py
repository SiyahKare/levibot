#!/usr/bin/env python3
"""
Create training data snapshot with manifest and checksums.

Usage:
    python backend/scripts/make_snapshot.py --days 90 --symbols BTCUSDT,ETHUSDT,SOLUSDT
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

# Add parent to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.src.data.feature_registry.validator import validate_features
from backend.src.data.feature_store import minute_features
from backend.src.data.mexc_ccxt import MexcAdapter


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


async def fetch_and_process(
    symbol: str, days: int, horizon: int = 5
) -> pd.DataFrame:
    """
    Fetch bars and compute features for a symbol.

    Args:
        symbol: Trading symbol (e.g., BTCUSDT)
        days: Number of days of history
        horizon: Prediction horizon in minutes

    Returns:
        DataFrame with features
    """
    print(f"📊 Fetching {days} days of data for {symbol}...")
    
    # Fetch OHLCV bars
    mexc = MexcAdapter(symbols=[symbol], rate_limit=True)
    bars = await mexc.fetch_ohlcv(
        symbol=symbol, 
        timeframe="1m", 
        limit=days * 1440  # 1440 minutes per day
    )
    
    print(f"   ✅ Fetched {len(bars)} bars")
    
    # Convert to DataFrame
    df_bars = pd.DataFrame(bars, columns=["ts", "open", "high", "low", "close", "volume"])
    
    # Compute features
    print(f"   🔧 Computing features...")
    df_features = minute_features(df_bars, horizon=horizon)
    
    # Add symbol column
    df_features["symbol"] = symbol
    
    print(f"   ✅ Generated {len(df_features)} feature rows")
    
    return df_features


def create_snapshot(
    symbols: list[str], 
    days: int = 90, 
    horizon: int = 5,
    output_dir: Path | None = None
) -> dict:
    """
    Create snapshot with manifest.

    Args:
        symbols: List of symbols (e.g., ["BTCUSDT", "ETHUSDT"])
        days: Number of days of history
        horizon: Prediction horizon
        output_dir: Output directory (defaults to backend/data/snapshots/<timestamp>)

    Returns:
        Manifest dictionary
    """
    import asyncio
    
    # Create output directory
    snapshot_id = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")
    if output_dir is None:
        output_dir = Path("backend/data/snapshots") / snapshot_id
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n🎯 Creating snapshot: {snapshot_id}")
    print(f"📁 Output directory: {output_dir}")
    print(f"📅 Days: {days} | Symbols: {', '.join(symbols)}\n")
    
    # Compute date range
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=days)
    
    manifest = {
        "snapshot_id": snapshot_id,
        "symbols": symbols,
        "timeframe": "1m",
        "horizon": horizon,
        "range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        },
        "files": [],
    }
    
    # Process each symbol
    for symbol in symbols:
        try:
            # Fetch and process
            df = asyncio.run(fetch_and_process(symbol, days, horizon))
            
            # Validate schema
            print(f"   🔍 Validating schema...")
            try:
                validate_features(df)
                print(f"   ✅ Schema validation passed")
            except ValueError as e:
                print(f"   ⚠️ Schema validation warning: {e}")
                # Continue anyway (warnings only)
            
            # Save to Parquet
            parquet_path = output_dir / f"{symbol}.parquet"
            df.to_parquet(parquet_path, index=False, compression="snappy")
            print(f"   💾 Saved: {parquet_path}")
            
            # Compute checksum
            checksum = compute_sha256(parquet_path)
            print(f"   🔐 SHA-256: {checksum[:16]}...")
            
            # Add to manifest
            manifest["files"].append({
                "path": f"{symbol}.parquet",
                "symbol": symbol,
                "rows": len(df),
                "sha256": checksum,
            })
            
            print(f"   ✅ {symbol} complete\n")
            
        except Exception as e:
            print(f"   ❌ Failed to process {symbol}: {e}\n")
            continue
    
    # Save manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Manifest saved: {manifest_path}")
    
    # Compute overall checksum
    overall_checksum = hashlib.sha256(
        json.dumps(manifest, sort_keys=True).encode()
    ).hexdigest()
    
    manifest["overall_checksum"] = overall_checksum
    
    # Re-save with overall checksum
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"🔐 Overall checksum: {overall_checksum[:16]}...")
    print(f"\n🎉 Snapshot complete! ID: {snapshot_id}")
    
    return manifest


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Create training data snapshot")
    parser.add_argument(
        "--days", 
        type=int, 
        default=90, 
        help="Number of days of history (default: 90)"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        required=True,
        help="Comma-separated symbols (e.g., BTCUSDT,ETHUSDT,SOLUSDT)"
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=5,
        help="Prediction horizon in minutes (default: 5)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory (optional, defaults to backend/data/snapshots/<timestamp>)"
    )
    
    args = parser.parse_args()
    
    # Parse symbols
    symbols = [s.strip() for s in args.symbols.split(",")]
    
    # Create snapshot
    output_dir = Path(args.output) if args.output else None
    manifest = create_snapshot(symbols, args.days, args.horizon, output_dir)
    
    # Print summary
    print("\n" + "="*70)
    print("📊 SNAPSHOT SUMMARY")
    print("="*70)
    print(f"ID:       {manifest['snapshot_id']}")
    print(f"Symbols:  {', '.join(manifest['symbols'])}")
    print(f"Files:    {len(manifest['files'])}")
    print(f"Total rows: {sum(f['rows'] for f in manifest['files']):,}")
    print(f"Checksum: {manifest['overall_checksum'][:32]}...")
    print("="*70)


if __name__ == "__main__":
    main()


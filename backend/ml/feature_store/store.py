"""
Feature Store - DuckDB Backend

High-performance feature storage with Parquet persistence.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import polars as pl


class FeatureStore:
    """
    DuckDB-based feature store with Parquet backend.
    
    Features:
    - Fast read/write with DuckDB
    - Parquet persistence
    - Time-series optimized
    - Schema versioning
    """
    
    def __init__(self, data_dir: str | None = None):
        if data_dir is None:
            data_dir = os.getenv("FEATURE_STORE_PATH", "backend/data/features")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # DuckDB connection (in-memory with parquet views)
        self.conn = duckdb.connect(":memory:")
        
        # Initialize tables
        self._init_schema()
    
    def _init_schema(self):
        """Initialize feature store schema."""
        # Features table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS features (
                symbol VARCHAR,
                timestamp TIMESTAMP,
                timeframe VARCHAR,
                -- Price/Volume
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                -- Returns
                ret_1 DOUBLE,
                ret_3 DOUBLE,
                ret_6 DOUBLE,
                ret_12 DOUBLE,
                -- Technical Indicators
                rsi_14 DOUBLE,
                ema_21 DOUBLE,
                ema_55 DOUBLE,
                ema_200 DOUBLE,
                bb_upper DOUBLE,
                bb_lower DOUBLE,
                bb_pct DOUBLE,
                atr_14 DOUBLE,
                -- Volatility
                realized_vol_20 DOUBLE,
                z_score_20 DOUBLE,
                -- Derivatives (optional)
                funding_rate DOUBLE,
                oi_change_3 DOUBLE,
                long_short_ratio DOUBLE,
                -- Sentiment (optional)
                news_impact DOUBLE,
                news_confidence DOUBLE,
                -- Regime
                regime_vol VARCHAR,
                regime_trend VARCHAR,
                -- Label (for training)
                label_return_3 DOUBLE,
                label_direction INT,  -- -1, 0, 1
                PRIMARY KEY (symbol, timestamp, timeframe)
            )
        """)
    
    def save_features(
        self,
        df: pl.DataFrame,
        symbol: str,
        timeframe: str = "15m",
    ) -> None:
        """
        Save features to store.
        
        Args:
            df: Polars DataFrame with features
            symbol: Trading symbol
            timeframe: Timeframe (e.g., '15m', '1h')
        """
        # Add metadata
        df = df.with_columns([
            pl.lit(symbol).alias("symbol"),
            pl.lit(timeframe).alias("timeframe"),
        ])
        
        # Insert into DuckDB
        self.conn.execute(
            "INSERT OR REPLACE INTO features SELECT * FROM df"
        )
        
        # Persist to Parquet
        parquet_path = self.data_dir / f"{symbol}_{timeframe}_features.parquet"
        df.write_parquet(parquet_path)
        
        print(f"✅ Saved {len(df)} features for {symbol} {timeframe}")
    
    def load_features(
        self,
        symbol: str,
        timeframe: str = "15m",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pl.DataFrame | None:
        """
        Load features from store.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_date: Start date filter
            end_date: End date filter
        
        Returns:
            Polars DataFrame or None
        """
        parquet_path = self.data_dir / f"{symbol}_{timeframe}_features.parquet"
        
        if not parquet_path.exists():
            return None
        
        # Load from Parquet (faster than DuckDB for single file)
        df = pl.read_parquet(parquet_path)
        
        # Apply filters
        if start_date:
            df = df.filter(pl.col("timestamp") >= start_date)
        if end_date:
            df = df.filter(pl.col("timestamp") <= end_date)
        
        return df
    
    def get_latest_features(
        self,
        symbol: str,
        timeframe: str = "15m",
        n: int = 1,
    ) -> pl.DataFrame | None:
        """
        Get latest N feature rows.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            n: Number of rows
        
        Returns:
            Polars DataFrame or None
        """
        df = self.load_features(symbol, timeframe)
        if df is None or len(df) == 0:
            return None
        
        return df.sort("timestamp").tail(n)
    
    def list_symbols(self) -> list[str]:
        """List all symbols in feature store."""
        files = list(self.data_dir.glob("*_features.parquet"))
        symbols = set()
        for f in files:
            # Extract symbol from filename (e.g., BTCUSDT_15m_features.parquet)
            parts = f.stem.split("_")
            if len(parts) >= 2:
                symbols.add(parts[0])
        return sorted(symbols)
    
    def get_stats(self) -> dict[str, Any]:
        """Get feature store statistics."""
        symbols = self.list_symbols()
        stats = {
            "total_symbols": len(symbols),
            "symbols": symbols,
            "storage_path": str(self.data_dir),
            "details": {},
        }
        
        for symbol in symbols:
            files = list(self.data_dir.glob(f"{symbol}_*_features.parquet"))
            total_rows = 0
            for f in files:
                try:
                    df = pl.read_parquet(f)
                    total_rows += len(df)
                except Exception:
                    pass
            stats["details"][symbol] = {"rows": total_rows}
        
        return stats
    
    def clear(self, symbol: str | None = None, timeframe: str | None = None):
        """
        Clear feature store data.
        
        Args:
            symbol: Clear specific symbol (None = all)
            timeframe: Clear specific timeframe (None = all)
        """
        if symbol and timeframe:
            path = self.data_dir / f"{symbol}_{timeframe}_features.parquet"
            if path.exists():
                path.unlink()
        elif symbol:
            for f in self.data_dir.glob(f"{symbol}_*_features.parquet"):
                f.unlink()
        else:
            for f in self.data_dir.glob("*_features.parquet"):
                f.unlink()
        
        # Clear DuckDB
        self.conn.execute("DELETE FROM features")
    
    def close(self):
        """Close DuckDB connection."""
        self.conn.close()


# Global instance
_STORE: FeatureStore | None = None


def get_feature_store() -> FeatureStore:
    """Get or create global feature store instance."""
    global _STORE
    if _STORE is None:
        _STORE = FeatureStore()
    return _STORE


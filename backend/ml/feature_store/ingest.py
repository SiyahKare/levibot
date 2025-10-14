"""
Data Ingestor

Fetch OHLCV data from exchanges (CCXT) and persist.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta

import ccxt
import polars as pl


class DataIngestor:
    """
    Fetch historical OHLCV data from exchanges.
    
    Supports:
    - Multiple exchanges (Binance, MEXC, etc.)
    - Multiple timeframes
    - Rate limiting
    - Incremental updates
    """
    
    def __init__(self, exchange_id: str = "binance"):
        """
        Initialize data ingestor.
        
        Args:
            exchange_id: Exchange ID (binance, mexc, bybit, etc.)
        """
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "15m",
        since: datetime | None = None,
        limit: int = 1000,
    ) -> pl.DataFrame:
        """
        Fetch OHLCV data.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            since: Start datetime
            limit: Number of candles
        
        Returns:
            Polars DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Convert symbol format
        if "/" not in symbol:
            # BTCUSDT -> BTC/USDT
            if symbol.endswith("USDT"):
                symbol = symbol[:-4] + "/USDT"
            elif symbol.endswith("USD"):
                symbol = symbol[:-3] + "/USD"
        
        # Convert datetime to milliseconds
        since_ms = None
        if since:
            since_ms = int(since.timestamp() * 1000)
        
        try:
            # Fetch from exchange
            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=since_ms,
                limit=limit,
            )
            
            if not ohlcv:
                return pl.DataFrame()
            
            # Convert to Polars DataFrame
            df = pl.DataFrame({
                "timestamp": [datetime.fromtimestamp(row[0] / 1000) for row in ohlcv],
                "open": [float(row[1]) for row in ohlcv],
                "high": [float(row[2]) for row in ohlcv],
                "low": [float(row[3]) for row in ohlcv],
                "close": [float(row[4]) for row in ohlcv],
                "volume": [float(row[5]) for row in ohlcv],
            })
            
            return df
        
        except Exception as e:
            print(f"⚠️  Failed to fetch {symbol} {timeframe}: {e}")
            return pl.DataFrame()
    
    def fetch_historical(
        self,
        symbol: str,
        timeframe: str = "15m",
        days: int = 30,
    ) -> pl.DataFrame:
        """
        Fetch historical data for multiple days.
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            days: Number of days to fetch
        
        Returns:
            Combined Polars DataFrame
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        all_data = []
        current_time = start_time
        
        print(f"📥 Fetching {symbol} {timeframe} for {days} days...")
        
        while current_time < end_time:
            df = self.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                since=current_time,
                limit=1000,
            )
            
            if df is None or len(df) == 0:
                break
            
            all_data.append(df)
            
            # Move to next batch
            last_time = df["timestamp"].max()
            current_time = last_time + timedelta(minutes=1)
            
            # Rate limiting
            time.sleep(0.5)
            
            print(f"  📦 Fetched {len(df)} candles (up to {last_time})")
        
        if not all_data:
            return pl.DataFrame()
        
        # Combine and deduplicate
        combined = pl.concat(all_data)
        combined = combined.unique(subset=["timestamp"]).sort("timestamp")
        
        print(f"✅ Total: {len(combined)} candles")
        
        return combined
    
    def fetch_funding_rate(
        self,
        symbol: str,
        since: datetime | None = None,
        limit: int = 100,
    ) -> pl.DataFrame:
        """
        Fetch funding rate history (for perpetual futures).
        
        Args:
            symbol: Trading symbol
            since: Start datetime
            limit: Number of records
        
        Returns:
            Polars DataFrame with funding rate data
        """
        # Convert symbol format
        if "/" not in symbol:
            if symbol.endswith("USDT"):
                symbol = symbol[:-4] + "/USDT"
        
        try:
            # Check if exchange supports funding rates
            if not hasattr(self.exchange, "fetch_funding_rate_history"):
                print(f"⚠️  {self.exchange_id} doesn't support funding rate history")
                return pl.DataFrame()
            
            since_ms = None
            if since:
                since_ms = int(since.timestamp() * 1000)
            
            funding = self.exchange.fetch_funding_rate_history(
                symbol,
                since=since_ms,
                limit=limit,
            )
            
            if not funding:
                return pl.DataFrame()
            
            df = pl.DataFrame({
                "timestamp": [datetime.fromtimestamp(r["timestamp"] / 1000) for r in funding],
                "funding_rate": [float(r["fundingRate"]) for r in funding],
            })
            
            return df
        
        except Exception as e:
            print(f"⚠️  Failed to fetch funding rate for {symbol}: {e}")
            return pl.DataFrame()
    
    def fetch_current_price(self, symbol: str) -> float | None:
        """
        Fetch current price.
        
        Args:
            symbol: Trading symbol
        
        Returns:
            Current price or None
        """
        if "/" not in symbol:
            if symbol.endswith("USDT"):
                symbol = symbol[:-4] + "/USDT"
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker["last"])
        except Exception as e:
            print(f"⚠️  Failed to fetch price for {symbol}: {e}")
            return None
    
    def close(self):
        """Close exchange connection."""
        if hasattr(self.exchange, "close"):
            self.exchange.close()


def fetch_and_store(
    symbol: str,
    timeframe: str = "15m",
    days: int = 30,
    exchange_id: str = "binance",
) -> pl.DataFrame:
    """
    Convenience function to fetch and return data.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe
        days: Number of days
        exchange_id: Exchange ID
    
    Returns:
        Polars DataFrame with OHLCV data
    """
    ingestor = DataIngestor(exchange_id=exchange_id)
    df = ingestor.fetch_historical(symbol=symbol, timeframe=timeframe, days=days)
    ingestor.close()
    return df


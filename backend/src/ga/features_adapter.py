"""Features adapter for LeviBot integration."""

import logging
from pathlib import Path

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


def load_panel(
    symbols: list[str], timeframe: str = "1m", days: int = 90
) -> dict[str, pd.DataFrame]:
    """
    Load market data panel from LeviBot's feature store.

    Args:
        symbols: List of trading symbols
        timeframe: Data timeframe (1m, 5m, etc.)
        days: Number of days to load

    Returns:
        Dictionary mapping symbol to DataFrame
    """
    db_path = "backend/data/analytics.duckdb"

    if not Path(db_path).exists():
        logger.warning(f"Database not found at {db_path}, creating empty data")
        return _create_mock_data(symbols, timeframe, days)

    try:
        con = duckdb.connect(database=db_path, read_only=True)
        out = {}

        for sym in symbols:
            try:
                # Try to load from ohlcv table first
                df = con.execute(
                    f"""
                    SELECT * FROM ohlcv
                    WHERE symbol = '{sym}' AND timeframe = '{timeframe}'
                    AND ts >= NOW() - INTERVAL {days} DAY
                    ORDER BY ts
                """
                ).df()

                if not df.empty:
                    df = df.set_index("ts")
                    out[sym] = df
                    logger.info(f"Loaded {len(df)} bars for {sym}")
                    continue

                # Fallback: try to load from any table with OHLCV data
                tables = con.execute("SHOW TABLES").df()
                logger.info(f"Available tables: {tables['name'].tolist()}")

                # Try to find data in any table
                for table_name in tables["name"]:
                    try:
                        df = con.execute(
                            f"""
                            SELECT * FROM {table_name}
                            WHERE symbol = '{sym}'
                            ORDER BY ts
                            LIMIT 1000
                        """
                        ).df()

                        if not df.empty and "close" in df.columns:
                            df = df.set_index("ts") if "ts" in df.columns else df
                            out[sym] = df
                            logger.info(
                                f"Loaded {len(df)} bars for {sym} from {table_name}"
                            )
                            break
                    except Exception as e:
                        logger.debug(f"Failed to load from {table_name}: {e}")
                        continue

                if sym not in out:
                    logger.warning(f"No data found for {sym}, creating mock data")
                    out[sym] = _create_mock_symbol_data(sym, timeframe, days)

            except Exception as e:
                logger.error(f"Error loading data for {sym}: {e}")
                out[sym] = _create_mock_symbol_data(sym, timeframe, days)

        con.close()
        return out

    except Exception as e:
        logger.error(f"Database error: {e}")
        return _create_mock_data(symbols, timeframe, days)


def _create_mock_data(
    symbols: list[str], timeframe: str, days: int
) -> dict[str, pd.DataFrame]:
    """Create mock data for testing."""
    out = {}
    for sym in symbols:
        out[sym] = _create_mock_symbol_data(sym, timeframe, days)
    return out


def _create_mock_symbol_data(symbol: str, timeframe: str, days: int) -> pd.DataFrame:
    """Create mock data for a single symbol."""
    from datetime import datetime, timedelta

    import numpy as np

    # Generate timestamps
    if timeframe == "1m":
        freq = "1min"
    elif timeframe == "5m":
        freq = "5min"
    else:
        freq = "1min"

    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)

    timestamps = pd.date_range(start=start_time, end=end_time, freq=freq)

    # Generate mock OHLCV data
    n = len(timestamps)
    base_price = 50000 if "BTC" in symbol else 3000 if "ETH" in symbol else 100

    # Random walk
    returns = np.random.normal(0, 0.001, n)
    prices = base_price * np.exp(np.cumsum(returns))

    # OHLCV
    df = pd.DataFrame(
        {
            "open": prices,
            "high": prices * (1 + np.abs(np.random.normal(0, 0.002, n))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.002, n))),
            "close": prices,
            "volume": np.random.uniform(1000, 10000, n),
            "symbol": symbol,
            "timeframe": timeframe,
        },
        index=timestamps,
    )

    # Ensure high >= low
    df["high"] = np.maximum(df["high"], df[["open", "close"]].max(axis=1))
    df["low"] = np.minimum(df["low"], df[["open", "close"]].min(axis=1))

    return df


def load_features_from_parquet(symbol: str, days: int = 90) -> pd.DataFrame | None:
    """
    Load features from Parquet files (LeviBot feature store).

    Args:
        symbol: Trading symbol
        days: Number of days to load

    Returns:
        DataFrame with features or None if not found
    """
    parquet_dir = Path("backend/data/features")

    if not parquet_dir.exists():
        logger.warning(f"Features directory not found: {parquet_dir}")
        return None

    # Look for symbol-specific parquet files
    pattern = f"*{symbol.replace('/', '_')}*.parquet"
    files = list(parquet_dir.glob(pattern))

    if not files:
        logger.warning(f"No parquet files found for {symbol}")
        return None

    # Load the most recent file
    latest_file = max(files, key=lambda x: x.stat().st_mtime)

    try:
        df = pd.read_parquet(latest_file)

        # Filter by date if ts column exists
        if "ts" in df.columns:
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
            df = df[df["ts"] >= cutoff]

        logger.info(f"Loaded {len(df)} feature rows for {symbol} from {latest_file}")
        return df

    except Exception as e:
        logger.error(f"Error loading parquet file {latest_file}: {e}")
        return None


def get_available_symbols() -> list[str]:
    """Get list of available symbols from the database."""
    db_path = "backend/data/analytics.duckdb"

    if not Path(db_path).exists():
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    try:
        con = duckdb.connect(database=db_path, read_only=True)

        # Try to get symbols from ohlcv table
        try:
            symbols = (
                con.execute("SELECT DISTINCT symbol FROM ohlcv").df()["symbol"].tolist()
            )
            con.close()
            return symbols
        except:
            pass

        # Fallback: return default symbols
        con.close()
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

    except Exception as e:
        logger.error(f"Error getting available symbols: {e}")
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT"]

"""
ClickHouse Client - High-performance timeseries storage
Optimized for analytics, dashboards, and ML feature queries
"""
import os
from datetime import datetime

import clickhouse_connect
from clickhouse_connect.driver import Client


class ClickHouseClient:
    """
    ClickHouse client for timeseries data
    
    Features:
    - Async bulk inserts
    - Materialized views for aggregations
    - Partitioning by date
    - TTL for data retention
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8123,
        database: str = "levibot",
        username: str = "default",
        password: str = ""
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self._client: Client | None = None
    
    def connect(self) -> Client:
        """Get or create ClickHouse client"""
        if self._client is None:
            self._client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database
            )
        return self._client
    
    def init_schema(self):
        """Initialize database schema"""
        client = self.connect()
        
        # Create database
        client.command(f"CREATE DATABASE IF NOT EXISTS {self.database}")
        
        # OHLCV table
        client.command("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                ts DateTime,
                venue LowCardinality(String),
                symbol LowCardinality(String),
                tf LowCardinality(String),
                open Float64,
                high Float64,
                low Float64,
                close Float64,
                volume Float64,
                trades UInt32
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(ts)
            ORDER BY (symbol, tf, ts)
            TTL ts + INTERVAL 90 DAY
        """)
        
        # Features table
        client.command("""
            CREATE TABLE IF NOT EXISTS features (
                ts DateTime,
                symbol LowCardinality(String),
                tf LowCardinality(String),
                -- Price features
                vwap_dev Float32,
                zscore Float32,
                atr Float32,
                rsi Float32,
                -- Volume features
                vol_ratio Float32,
                vol_imbalance Float32,
                -- Microstructure
                spread_bps Float32,
                ofi Float32,
                -- Regime
                regime UInt8,
                volatility_regime UInt8
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(ts)
            ORDER BY (symbol, tf, ts)
            TTL ts + INTERVAL 90 DAY
        """)
        
        # Signals/Decisions table
        client.command("""
            CREATE TABLE IF NOT EXISTS signals (
                ts DateTime,
                symbol LowCardinality(String),
                strategy LowCardinality(String),
                side Int8,
                confidence Float32,
                reason String,
                metadata String,
                signal_id UUID DEFAULT generateUUIDv4()
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(ts)
            ORDER BY (symbol, strategy, ts)
            TTL ts + INTERVAL 180 DAY
        """)
        
        # Orders table
        client.command("""
            CREATE TABLE IF NOT EXISTS orders (
                ts DateTime,
                order_id String,
                symbol LowCardinality(String),
                side LowCardinality(String),
                type LowCardinality(String),
                quantity Float64,
                price Float64,
                status LowCardinality(String),
                filled_qty Float64,
                avg_fill_price Float64,
                commission Float64,
                latency_ms UInt32,
                metadata String
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(ts)
            ORDER BY (symbol, ts)
            TTL ts + INTERVAL 365 DAY
        """)
        
        # Fills table
        client.command("""
            CREATE TABLE IF NOT EXISTS fills (
                ts DateTime,
                fill_id String,
                order_id String,
                symbol LowCardinality(String),
                side LowCardinality(String),
                quantity Float64,
                price Float64,
                commission Float64,
                is_maker Bool
            ) ENGINE = MergeTree()
            PARTITION BY toYYYYMM(ts)
            ORDER BY (symbol, ts)
            TTL ts + INTERVAL 365 DAY
        """)
        
        # Equity/Performance table
        client.command("""
            CREATE TABLE IF NOT EXISTS equity (
                ts DateTime,
                equity Float64,
                cash_balance Float64,
                unrealized_pnl Float64,
                realized_pnl Float64,
                exposure Float64,
                num_positions UInt16,
                daily_pnl Float64,
                daily_return Float64,
                drawdown Float64
            ) ENGINE = MergeTree()
            ORDER BY ts
            TTL ts + INTERVAL 730 DAY
        """)
        
        # Materialized view for 1h OHLCV aggregation
        client.command("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_1h
            ENGINE = MergeTree()
            PARTITION BY toYYYYMM(ts_1h)
            ORDER BY (symbol, ts_1h)
            AS SELECT
                toStartOfHour(ts) as ts_1h,
                symbol,
                argMin(open, ts) as open,
                max(high) as high,
                min(low) as low,
                argMax(close, ts) as close,
                sum(volume) as volume,
                sum(trades) as trades
            FROM ohlcv
            WHERE tf = '1m'
            GROUP BY symbol, ts_1h
        """)
        
        # Materialized view for strategy performance
        client.command("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS strategy_performance
            ENGINE = SummingMergeTree()
            PARTITION BY toYYYYMM(date)
            ORDER BY (strategy, date)
            AS SELECT
                toDate(ts) as date,
                strategy,
                count() as num_signals,
                countIf(side = 1) as num_long,
                countIf(side = -1) as num_short,
                avg(confidence) as avg_confidence
            FROM signals
            GROUP BY date, strategy
        """)
        
        print("✅ ClickHouse schema initialized")
    
    def insert_ohlcv(self, data: list[dict]):
        """Bulk insert OHLCV data"""
        if not data:
            return
        
        client = self.connect()
        client.insert(
            "ohlcv",
            data,
            column_names=[
                "ts", "venue", "symbol", "tf",
                "open", "high", "low", "close", "volume", "trades"
            ]
        )
    
    def insert_features(self, data: list[dict]):
        """Bulk insert feature data"""
        if not data:
            return
        
        client = self.connect()
        client.insert("features", data)
    
    def insert_signal(
        self,
        symbol: str,
        strategy: str,
        side: int,
        confidence: float,
        reason: str,
        metadata: dict
    ):
        """Insert trading signal"""
        client = self.connect()
        client.insert(
            "signals",
            [{
                "ts": datetime.now(),
                "symbol": symbol,
                "strategy": strategy,
                "side": side,
                "confidence": confidence,
                "reason": reason,
                "metadata": str(metadata)
            }]
        )
    
    def insert_equity_snapshot(
        self,
        equity: float,
        cash_balance: float,
        unrealized_pnl: float,
        realized_pnl: float,
        exposure: float,
        num_positions: int,
        daily_pnl: float,
        daily_return: float,
        drawdown: float
    ):
        """Insert equity snapshot"""
        client = self.connect()
        client.insert(
            "equity",
            [{
                "ts": datetime.now(),
                "equity": equity,
                "cash_balance": cash_balance,
                "unrealized_pnl": unrealized_pnl,
                "realized_pnl": realized_pnl,
                "exposure": exposure,
                "num_positions": num_positions,
                "daily_pnl": daily_pnl,
                "daily_return": daily_return,
                "drawdown": drawdown
            }]
        )
    
    def query_recent_signals(
        self,
        symbol: str | None = None,
        strategy: str | None = None,
        hours: int = 24,
        limit: int = 100
    ) -> list[dict]:
        """Query recent signals"""
        client = self.connect()
        
        where_clauses = [
            f"ts >= now() - INTERVAL {hours} HOUR"
        ]
        
        if symbol:
            where_clauses.append(f"symbol = '{symbol}'")
        if strategy:
            where_clauses.append(f"strategy = '{strategy}'")
        
        where_sql = " AND ".join(where_clauses)
        
        result = client.query(f"""
            SELECT
                ts,
                symbol,
                strategy,
                side,
                confidence,
                reason,
                metadata
            FROM signals
            WHERE {where_sql}
            ORDER BY ts DESC
            LIMIT {limit}
        """)
        
        return result.result_rows
    
    def query_equity_curve(
        self,
        hours: int = 24
    ) -> list[dict]:
        """Query equity curve"""
        client = self.connect()
        
        result = client.query(f"""
            SELECT
                ts,
                equity,
                realized_pnl,
                unrealized_pnl,
                exposure,
                drawdown
            FROM equity
            WHERE ts >= now() - INTERVAL {hours} HOUR
            ORDER BY ts ASC
        """)
        
        return [
            {
                "ts": row[0],
                "equity": row[1],
                "realized_pnl": row[2],
                "unrealized_pnl": row[3],
                "exposure": row[4],
                "drawdown": row[5]
            }
            for row in result.result_rows
        ]
    
    def query_strategy_stats(
        self,
        strategy: str,
        days: int = 7
    ) -> dict:
        """Query strategy performance statistics"""
        client = self.connect()
        
        result = client.query(f"""
            SELECT
                count() as num_signals,
                countIf(side = 1) as num_long,
                countIf(side = -1) as num_short,
                avg(confidence) as avg_confidence,
                min(confidence) as min_confidence,
                max(confidence) as max_confidence
            FROM signals
            WHERE strategy = '{strategy}'
              AND ts >= now() - INTERVAL {days} DAY
        """)
        
        row = result.result_rows[0]
        return {
            "num_signals": row[0],
            "num_long": row[1],
            "num_short": row[2],
            "avg_confidence": row[3],
            "min_confidence": row[4],
            "max_confidence": row[5]
        }


# Singleton instance
_client: ClickHouseClient | None = None


def get_clickhouse_client() -> ClickHouseClient:
    """Get global ClickHouse client instance"""
    global _client
    if _client is None:
        _client = ClickHouseClient(
            host=os.getenv("CLICKHOUSE_HOST", "localhost"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
            database=os.getenv("CLICKHOUSE_DB", "levibot"),
            username=os.getenv("CLICKHOUSE_USER", "default"),
            password=os.getenv("CLICKHOUSE_PASSWORD", "")
        )
    return _client


if __name__ == "__main__":
    # Initialize schema
    client = get_clickhouse_client()
    client.init_schema()
    
    # Test insert
    client.insert_signal(
        symbol="BTCUSDT",
        strategy="lse",
        side=1,
        confidence=0.65,
        reason="momentum_breakout",
        metadata={"atr": 150.5, "rsi": 62.3}
    )
    
    print("✅ Test signal inserted")
    
    # Query
    signals = client.query_recent_signals(limit=10)
    print(f"📊 Recent signals: {len(signals)}")


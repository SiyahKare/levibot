"""
Trades Repository - TimescaleDB persistence
Stores strategy trades and PnL data
"""
from datetime import datetime
from typing import Any

from psycopg2.pool import SimpleConnectionPool


class TradesRepository:
    """Repository for strategy trades persistence"""
    
    _pool: SimpleConnectionPool | None = None
    
    @classmethod
    def get_pool(cls) -> SimpleConnectionPool:
        """Get or create connection pool"""
        if cls._pool is None:
            import os
            
            cls._pool = SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "levibot"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
            )
            
            # Create table if not exists
            conn = cls._pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS strategy_trades (
                            id SERIAL PRIMARY KEY,
                            timestamp TIMESTAMPTZ NOT NULL,
                            strategy VARCHAR(50) NOT NULL,
                            symbol VARCHAR(20) NOT NULL,
                            side VARCHAR(10) NOT NULL,
                            action VARCHAR(20) NOT NULL,
                            price DOUBLE PRECISION NOT NULL,
                            qty DOUBLE PRECISION NOT NULL,
                            notional_usd DOUBLE PRECISION,
                            pnl_usd DOUBLE PRECISION,
                            pnl_pct DOUBLE PRECISION,
                            reason VARCHAR(100),
                            mode VARCHAR(10),
                            metadata JSONB
                        );
                        
                        -- Create hypertable if not already
                        SELECT create_hypertable(
                            'strategy_trades', 
                            'timestamp',
                            if_not_exists => TRUE
                        );
                        
                        -- Index for querying (timestamp must be part of all indexes on hypertables)
                        CREATE INDEX IF NOT EXISTS idx_strategy_trades_strategy_time 
                        ON strategy_trades (timestamp DESC, strategy);
                        
                        CREATE INDEX IF NOT EXISTS idx_strategy_trades_symbol 
                        ON strategy_trades (timestamp DESC, symbol);
                    """)
                    conn.commit()
            finally:
                cls._pool.putconn(conn)
        
        return cls._pool
    
    @classmethod
    def log_trade(
        cls,
        strategy: str,
        symbol: str,
        side: str,
        action: str,
        price: float,
        qty: float,
        notional_usd: float | None = None,
        pnl_usd: float | None = None,
        pnl_pct: float | None = None,
        reason: str | None = None,
        mode: str = "paper",
        metadata: dict | None = None,
        timestamp: datetime | None = None
    ) -> int:
        """
        Log a trade to database.
        
        Args:
            strategy: Strategy name (lse, day, swing)
            symbol: Trading symbol
            side: long/short
            action: enter_long, exit_position, etc.
            price: Execution price
            qty: Quantity
            notional_usd: Notional value in USD
            pnl_usd: PnL in USD (for exits)
            pnl_pct: PnL percentage (for exits)
            reason: Trade reason (signal, stop_loss, take_profit)
            mode: paper/real
            metadata: Additional metadata as JSON
            timestamp: Trade timestamp (defaults to now)
        
        Returns:
            Trade ID
        """
        pool = cls.get_pool()
        conn = pool.getconn()
        
        try:
            with conn.cursor() as cur:
                ts = timestamp or datetime.now()
                
                cur.execute(
                    """
                    INSERT INTO strategy_trades (
                        timestamp, strategy, symbol, side, action,
                        price, qty, notional_usd, pnl_usd, pnl_pct,
                        reason, mode, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    ) RETURNING id
                    """,
                    (
                        ts, strategy, symbol, side, action,
                        price, qty, notional_usd, pnl_usd, pnl_pct,
                        reason, mode, metadata
                    )
                )
                
                trade_id = cur.fetchone()[0]
                conn.commit()
                return trade_id
        finally:
            pool.putconn(conn)
    
    @classmethod
    def get_recent_trades(
        cls,
        strategy: str | None = None,
        symbol: str | None = None,
        limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get recent trades.
        
        Args:
            strategy: Filter by strategy (optional)
            symbol: Filter by symbol (optional)
            limit: Max number of trades
        
        Returns:
            List of trade dicts
        """
        pool = cls.get_pool()
        conn = pool.getconn()
        
        try:
            with conn.cursor() as cur:
                query = "SELECT * FROM strategy_trades WHERE 1=1"
                params = []
                
                if strategy:
                    query += " AND strategy = %s"
                    params.append(strategy)
                
                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol)
                
                query += " ORDER BY timestamp DESC LIMIT %s"
                params.append(limit)
                
                cur.execute(query, params)
                
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        finally:
            pool.putconn(conn)
    
    @classmethod
    def get_pnl_stats(
        cls,
        strategy: str,
        symbol: str | None = None,
        hours: int = 24
    ) -> dict[str, Any]:
        """
        Get PnL statistics for a strategy.
        
        Args:
            strategy: Strategy name
            symbol: Filter by symbol (optional)
            hours: Time window in hours
        
        Returns:
            PnL stats dict
        """
        pool = cls.get_pool()
        conn = pool.getconn()
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT
                        COUNT(*) FILTER (WHERE action LIKE '%exit%') as total_trades,
                        SUM(pnl_usd) as total_pnl,
                        AVG(pnl_usd) FILTER (WHERE pnl_usd IS NOT NULL) as avg_pnl,
                        COUNT(*) FILTER (WHERE pnl_usd > 0) as winning_trades,
                        COUNT(*) FILTER (WHERE pnl_usd < 0) as losing_trades,
                        MAX(pnl_usd) as best_trade,
                        MIN(pnl_usd) as worst_trade
                    FROM strategy_trades
                    WHERE strategy = %s
                        AND timestamp > NOW() - INTERVAL '%s hours'
                """
                params = [strategy, hours]
                
                if symbol:
                    query += " AND symbol = %s"
                    params.append(symbol)
                
                cur.execute(query, params)
                row = cur.fetchone()
                
                total_trades = row[0] or 0
                win_rate = (row[3] / total_trades * 100) if total_trades > 0 else 0.0
                
                return {
                    "total_trades": total_trades,
                    "total_pnl": float(row[1]) if row[1] else 0.0,
                    "avg_pnl": float(row[2]) if row[2] else 0.0,
                    "winning_trades": row[3] or 0,
                    "losing_trades": row[4] or 0,
                    "win_rate": win_rate,
                    "best_trade": float(row[5]) if row[5] else 0.0,
                    "worst_trade": float(row[6]) if row[6] else 0.0,
                }
        finally:
            pool.putconn(conn)


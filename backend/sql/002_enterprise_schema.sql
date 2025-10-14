-- ═══════════════════════════════════════════════════════════════
-- LeviBot Enterprise - ClickHouse Schema
-- ═══════════════════════════════════════════════════════════════

-- Market Data Tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS levibot.ohlcv (
    timestamp DateTime64(3),
    symbol String,
    exchange String,
    timeframe String,
    open Float64,
    high Float64,
    low Float64,
    close Float64,
    volume Float64,
    quote_volume Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
TTL timestamp + INTERVAL 90 DAY;

CREATE TABLE IF NOT EXISTS levibot.trades (
    timestamp DateTime64(3),
    symbol String,
    exchange String,
    trade_id String,
    side String,
    price Float64,
    amount Float64,
    cost Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
TTL timestamp + INTERVAL 30 DAY;

CREATE TABLE IF NOT EXISTS levibot.orderbook_l2 (
    timestamp DateTime64(3),
    symbol String,
    exchange String,
    bids Array(Tuple(Float64, Float64)),
    asks Array(Tuple(Float64, Float64)),
    bid_volume Float64,
    ask_volume Float64,
    spread Float64
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
TTL timestamp + INTERVAL 7 DAY;

CREATE TABLE IF NOT EXISTS levibot.funding_rates (
    timestamp DateTime64(3),
    symbol String,
    exchange String,
    funding_rate Float64,
    next_funding_time DateTime64(3)
) ENGINE = ReplacingMergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);

-- Feature Store Tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS levibot.features (
    timestamp DateTime64(3),
    symbol String,
    feature_name String,
    feature_value Float64,
    feature_version String DEFAULT 'v1'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, feature_name, timestamp)
TTL timestamp + INTERVAL 30 DAY;

-- Signal & Decision Tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS levibot.signals (
    timestamp DateTime64(3),
    symbol String,
    strategy String,
    side Int8,
    confidence Float64,
    reason String,
    metadata String,
    policy_approved Bool DEFAULT false,
    policy_reason String DEFAULT ''
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);

CREATE TABLE IF NOT EXISTS levibot.decisions (
    timestamp DateTime64(3),
    symbol String,
    decision_type String,
    action String,
    quantity Float64,
    price Float64,
    reason String,
    metadata String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);

-- Execution Tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS levibot.orders (
    timestamp DateTime64(3),
    order_id String,
    symbol String,
    side String,
    type String,
    price Float64,
    amount Float64,
    status String,
    filled Float64 DEFAULT 0,
    remaining Float64,
    cost Float64 DEFAULT 0,
    fee Float64 DEFAULT 0,
    fee_currency String DEFAULT '',
    created_at DateTime64(3),
    updated_at DateTime64(3),
    metadata String DEFAULT '{}'
) ENGINE = ReplacingMergeTree(updated_at)
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, order_id, timestamp);

CREATE TABLE IF NOT EXISTS levibot.fills (
    timestamp DateTime64(3),
    fill_id String,
    order_id String,
    symbol String,
    side String,
    price Float64,
    amount Float64,
    cost Float64,
    fee Float64,
    fee_currency String,
    trade_id String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, order_id, timestamp);

-- Portfolio & Performance Tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS levibot.portfolio_snapshots (
    timestamp DateTime64(3),
    equity Float64,
    cash Float64,
    positions_value Float64,
    unrealized_pnl Float64,
    realized_pnl Float64,
    daily_pnl Float64,
    total_pnl Float64,
    num_positions Int32,
    leverage Float64 DEFAULT 1.0
) ENGINE = ReplacingMergeTree(timestamp)
ORDER BY timestamp;

CREATE TABLE IF NOT EXISTS levibot.positions (
    timestamp DateTime64(3),
    symbol String,
    side String,
    size Float64,
    entry_price Float64,
    current_price Float64,
    unrealized_pnl Float64,
    realized_pnl Float64,
    leverage Float64 DEFAULT 1.0,
    liquidation_price Float64 DEFAULT 0
) ENGINE = ReplacingMergeTree(timestamp)
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp);

-- Audit & Compliance Tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS levibot.audit_log (
    timestamp DateTime64(3),
    event_type String,
    user_id String,
    action String,
    resource String,
    details String,
    ip_address String DEFAULT '',
    user_agent String DEFAULT ''
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_type, timestamp)
TTL timestamp + INTERVAL 365 DAY;

CREATE TABLE IF NOT EXISTS levibot.alerts (
    timestamp DateTime64(3),
    alert_type String,
    severity String,
    title String,
    message String,
    metadata String DEFAULT '{}',
    acknowledged Bool DEFAULT false,
    acknowledged_at DateTime64(3) DEFAULT toDateTime64('1970-01-01 00:00:00', 3),
    acknowledged_by String DEFAULT ''
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (severity, timestamp);

-- System Metrics Tables
-- ─────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS levibot.system_metrics (
    timestamp DateTime64(3),
    metric_name String,
    metric_value Float64,
    service String,
    labels String DEFAULT '{}'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service, metric_name, timestamp)
TTL timestamp + INTERVAL 30 DAY;

-- Materialized Views for Analytics
-- ─────────────────────────────────────────────────────────────

-- Hourly OHLCV aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS levibot.ohlcv_1h
ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
AS SELECT
    toStartOfHour(timestamp) as timestamp,
    symbol,
    exchange,
    '1h' as timeframe,
    argMin(open, timestamp) as open,
    max(high) as high,
    min(low) as low,
    argMax(close, timestamp) as close,
    sum(volume) as volume,
    sum(quote_volume) as quote_volume
FROM levibot.ohlcv
WHERE timeframe = '1m'
GROUP BY symbol, exchange, timestamp;

-- Daily performance summary
CREATE MATERIALIZED VIEW IF NOT EXISTS levibot.daily_performance
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, symbol)
AS SELECT
    toDate(timestamp) as date,
    symbol,
    count() as num_trades,
    sum(CASE WHEN side = 'buy' THEN 1 ELSE 0 END) as num_buys,
    sum(CASE WHEN side = 'sell' THEN 1 ELSE 0 END) as num_sells,
    sum(cost) as total_volume,
    sum(fee) as total_fees
FROM levibot.fills
GROUP BY date, symbol;

-- Signal performance tracking
CREATE MATERIALIZED VIEW IF NOT EXISTS levibot.signal_performance
ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, strategy, symbol)
AS SELECT
    toDate(timestamp) as date,
    strategy,
    symbol,
    count() as signal_count,
    avg(confidence) as avg_confidence,
    countIf(policy_approved) as approved_count,
    countIf(NOT policy_approved) as rejected_count
FROM levibot.signals
GROUP BY date, strategy, symbol;

-- ═══════════════════════════════════════════════════════════════
-- Indexes for Performance
-- ═══════════════════════════════════════════════════════════════

-- Skip indexes for faster queries
ALTER TABLE levibot.signals ADD INDEX idx_strategy strategy TYPE bloom_filter GRANULARITY 1;
ALTER TABLE levibot.orders ADD INDEX idx_status status TYPE set(10) GRANULARITY 1;
ALTER TABLE levibot.audit_log ADD INDEX idx_event_type event_type TYPE bloom_filter GRANULARITY 1;

-- ═══════════════════════════════════════════════════════════════
-- Initial Data Seeding (Optional)
-- ═══════════════════════════════════════════════════════════════

-- Insert initial portfolio snapshot
INSERT INTO levibot.portfolio_snapshots (
    timestamp, equity, cash, positions_value, unrealized_pnl, 
    realized_pnl, daily_pnl, total_pnl, num_positions
) VALUES (
    now(), 10000.0, 10000.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0
);

-- Insert initial system health alert
INSERT INTO levibot.alerts (
    timestamp, alert_type, severity, title, message
) VALUES (
    now(), 'system', 'info', 'System Initialized', 
    'LeviBot Enterprise Platform has been successfully initialized'
);


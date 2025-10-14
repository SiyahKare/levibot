-- LEVIBOT TimescaleDB Schema
-- Realtime market data with hypertables and retention policies

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Market ticks (high frequency data)
CREATE TABLE IF NOT EXISTS market_ticks (
    ts TIMESTAMPTZ NOT NULL,
    venue TEXT NOT NULL,
    symbol TEXT NOT NULL,
    last NUMERIC,
    bid NUMERIC,
    ask NUMERIC,
    mark NUMERIC,
    volume NUMERIC,
    src TEXT
);

SELECT create_hypertable('market_ticks', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '1 day');

-- Equity curve (portfolio snapshots)
CREATE TABLE IF NOT EXISTS equity_curve (
    ts TIMESTAMPTZ NOT NULL,
    balance NUMERIC NOT NULL,
    realized NUMERIC NOT NULL,
    unrealized NUMERIC NOT NULL,
    drawdown NUMERIC NOT NULL,
    equity NUMERIC NOT NULL
);

SELECT create_hypertable('equity_curve', 'ts', if_not_exists => TRUE, chunk_time_interval => INTERVAL '7 days');

-- Orders (all orders including paper)
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty NUMERIC NOT NULL,
    price NUMERIC,
    fee NUMERIC DEFAULT 0,
    type TEXT DEFAULT 'market',
    status TEXT DEFAULT 'new',
    is_paper BOOLEAN DEFAULT TRUE,
    trace_id TEXT
);

CREATE INDEX IF NOT EXISTS orders_ts_idx ON orders(ts DESC);
CREATE INDEX IF NOT EXISTS orders_symbol_idx ON orders(symbol);

-- Trades (filled orders)
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    qty NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    fee NUMERIC DEFAULT 0,
    is_paper BOOLEAN DEFAULT TRUE,
    pnl NUMERIC DEFAULT 0,
    trace_id TEXT
);

CREATE INDEX IF NOT EXISTS trades_ts_idx ON trades(ts DESC);
CREATE INDEX IF NOT EXISTS trades_symbol_idx ON trades(symbol);

-- Signals (trading signals from any source)
CREATE TABLE IF NOT EXISTS signals (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    size NUMERIC,
    sl NUMERIC,
    tp NUMERIC,
    confidence NUMERIC DEFAULT 0,
    rationale TEXT,
    executed BOOLEAN DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS signals_ts_idx ON signals(ts DESC);
CREATE INDEX IF NOT EXISTS signals_symbol_idx ON signals(symbol);

-- Retention policies (auto-cleanup old data)
SELECT add_retention_policy('market_ticks', INTERVAL '60 days', if_not_exists => TRUE);

-- Compression policies (save space on old chunks)
SELECT add_compression_policy('market_ticks', INTERVAL '7 days', if_not_exists => TRUE);








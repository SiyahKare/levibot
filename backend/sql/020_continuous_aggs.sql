-- Continuous Aggregates for Feature Engineering
-- Creates 1s and 5s candles for fast feature computation

-- =====================================================
-- 1-second candles (m1s)
-- =====================================================
DROP MATERIALIZED VIEW IF EXISTS m1s CASCADE;

CREATE MATERIALIZED VIEW m1s
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 second', ts) AS t,
    symbol,
    first(last, ts) AS open,
    last(last, ts) AS close,
    max(last) AS high,
    min(last) AS low,
    avg(last) AS avg_price,
    count(*) AS tick_count
FROM market_ticks
GROUP BY 1, 2;

-- Refresh policy: keep 2h history, refresh every 30s
SELECT add_continuous_aggregate_policy('m1s',
    start_offset => INTERVAL '2 hours',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '30 seconds');

-- Index for fast queries
CREATE INDEX IF NOT EXISTS idx_m1s_symbol_t ON m1s (symbol, t DESC);

-- =====================================================
-- 5-second candles (m5s)
-- =====================================================
DROP MATERIALIZED VIEW IF EXISTS m5s CASCADE;

CREATE MATERIALIZED VIEW m5s
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 seconds', ts) AS t,
    symbol,
    first(last, ts) AS open,
    last(last, ts) AS close,
    max(last) AS high,
    min(last) AS low,
    avg(last) AS avg_price,
    sum(vol) AS volume,
    count(*) AS tick_count
FROM market_ticks
GROUP BY 1, 2;

-- Refresh policy
SELECT add_continuous_aggregate_policy('m5s',
    start_offset => INTERVAL '6 hours',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '1 minute');

-- Index for fast queries
CREATE INDEX IF NOT EXISTS idx_m5s_symbol_t ON m5s (symbol, t DESC);

-- =====================================================
-- Verification queries
-- =====================================================

-- Check if data exists
-- SELECT symbol, count(*) FROM m1s WHERE t > now() - interval '1 hour' GROUP BY 1;
-- SELECT symbol, count(*) FROM m5s WHERE t > now() - interval '1 hour' GROUP BY 1;

-- Sample recent data
-- SELECT * FROM m1s WHERE symbol = 'BTCUSDT' ORDER BY t DESC LIMIT 10;


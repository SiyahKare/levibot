-- Continuous Aggregates (Real-time OHLCV Candles)

-- 1-second candles (for ultra-low latency)
CREATE MATERIALIZED VIEW IF NOT EXISTS candle_1s
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 second', ts) AS bucket,
    venue,
    symbol,
    first(last, ts) AS open,
    max(last) AS high,
    min(last) AS low,
    last(last, ts) AS close,
    sum(volume) AS volume,
    count(*) AS tick_count
FROM market_ticks
GROUP BY bucket, venue, symbol
WITH NO DATA;

-- Refresh policy: update every 1 second
SELECT add_continuous_aggregate_policy('candle_1s',
    start_offset => INTERVAL '10 seconds',
    end_offset => INTERVAL '1 second',
    schedule_interval => INTERVAL '1 second',
    if_not_exists => TRUE
);

-- 1-minute candles (standard)
CREATE MATERIALIZED VIEW IF NOT EXISTS candle_1m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 minute', ts) AS bucket,
    venue,
    symbol,
    first(last, ts) AS open,
    max(last) AS high,
    min(last) AS low,
    last(last, ts) AS close,
    sum(volume) AS volume,
    count(*) AS tick_count
FROM market_ticks
GROUP BY bucket, venue, symbol
WITH NO DATA;

-- Refresh policy: update every 10 seconds
SELECT add_continuous_aggregate_policy('candle_1m',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '10 seconds',
    if_not_exists => TRUE
);

-- 5-minute candles
CREATE MATERIALIZED VIEW IF NOT EXISTS candle_5m
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('5 minutes', ts) AS bucket,
    venue,
    symbol,
    first(last, ts) AS open,
    max(last) AS high,
    min(last) AS low,
    last(last, ts) AS close,
    sum(volume) AS volume,
    count(*) AS tick_count
FROM market_ticks
GROUP BY bucket, venue, symbol
WITH NO DATA;

SELECT add_continuous_aggregate_policy('candle_5m',
    start_offset => INTERVAL '6 hours',
    end_offset => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '30 seconds',
    if_not_exists => TRUE
);

-- Retention for aggregates
SELECT add_retention_policy('candle_1s', INTERVAL '7 days', if_not_exists => TRUE);
SELECT add_retention_policy('candle_1m', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('candle_5m', INTERVAL '1 year', if_not_exists => TRUE);








#!/usr/bin/env bash
# Keep market data fresh for testing (run every 60s)
docker compose exec -T timescaledb psql -U postgres -d levibot <<'SQL'
DO $$
DECLARE i INT;
BEGIN
    FOR i IN 0..60 LOOP
        INSERT INTO market_ticks(symbol, venue, ts, last, bid, ask)
        VALUES ('BTCUSDT', 'mexc', NOW() - (i * INTERVAL '1 second'), 61234.56 + (RANDOM()-0.5)*10, 61234.50, 61234.60),
               ('ETHUSDT', 'mexc', NOW() - (i * INTERVAL '1 second'), 3456.78 + (RANDOM()-0.5)*5, 3456.70, 3456.80)
        ON CONFLICT DO NOTHING;
    END LOOP;
END $$;
CALL refresh_continuous_aggregate('m1s', NOW() - INTERVAL '10 minutes', NOW());
SQL

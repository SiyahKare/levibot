#!/bin/bash
# Seed test data for model training
# Usage: ./seed_test_data.sh [num_samples]

set -e

SAMPLES=${1:-10000}
SYMBOL=${2:-BTCUSDT}

echo "🌱 Seeding $SAMPLES samples for $SYMBOL..."

docker compose exec -T timescaledb psql -U postgres -d levibot <<-SQL
  INSERT INTO market_ticks(symbol, ts, last, vol)
  SELECT 
    '$SYMBOL',
    NOW() - (i || ' seconds')::INTERVAL,
    50000 + (random() * 1000 - 500),  -- Random walk around 50k
    random() * 10  -- Random volume
  FROM generate_series(0, $SAMPLES) AS s(i);
  
  SELECT 
    symbol,
    COUNT(*) AS total_ticks,
    MIN(ts) AS earliest,
    MAX(ts) AS latest,
    EXTRACT(EPOCH FROM (MAX(ts) - MIN(ts))) AS span_seconds
  FROM market_ticks
  WHERE symbol = '$SYMBOL'
  GROUP BY symbol;
SQL

echo "✅ Seeded $SAMPLES ticks for $SYMBOL"
echo ""
echo "Next steps:"
echo "  1. Train model: make train-prod"
echo "  2. Restart backend: make backend-restart"
echo "  3. Test prediction: curl 'http://localhost:8000/ai/predict?symbol=$SYMBOL&h=60s'"


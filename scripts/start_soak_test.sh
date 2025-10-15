#!/bin/bash
#
# Start 24h soak test with all monitoring.
#
# Usage: ./scripts/start_soak_test.sh

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 Starting 24h Soak Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

API_URL="${API_URL:-http://localhost:8000}"
SYMBOLS="${SYMBOLS:-BTC/USDT,ETH/USDT,SOL/USDT,AVAX/USDT,OP/USDT}"

# 1. Pre-flight checks
echo -e "\n1️⃣ Pre-flight checks..."

# Check Docker
if ! docker ps > /dev/null 2>&1; then
  echo "   ❌ Docker not running!"
  exit 1
fi
echo "   ✅ Docker running"

# Check API
if ! curl -sf "$API_URL/health" > /dev/null; then
  echo "   ⚠️ API not responding, starting services..."
  docker compose up -d
  sleep 10
fi
echo "   ✅ API healthy"

# 2. Start engines
echo -e "\n2️⃣ Starting engines..."
IFS=',' read -ra SYMBOL_ARRAY <<< "$SYMBOLS"
for symbol in "${SYMBOL_ARRAY[@]}"; do
  echo "   Starting engine: $symbol"
  curl -s -X POST "$API_URL/engines/start?symbol=$symbol" > /dev/null || true
  sleep 2
done
echo "   ✅ Engines started"

# 3. Verify engine status
echo -e "\n3️⃣ Verifying engine status..."
ENGINES=$(curl -s "$API_URL/engines" | jq -r '.[] | select(.running == true) | .symbol' | wc -l)
echo "   Running engines: $ENGINES"

if [ "$ENGINES" -lt 3 ]; then
  echo "   ⚠️ WARNING: Less than 3 engines running!"
fi

# 4. Clear previous test data
echo -e "\n4️⃣ Clearing previous test data..."
rm -f reports/soak/soak_timeline.ndjson
rm -f reports/soak/soak_summary.json
echo "   ✅ Previous data cleared"

# 5. Start soak test
echo -e "\n5️⃣ Starting soak test (24h)..."
echo "   API URL: $API_URL"
echo "   Symbols: $SYMBOLS"
echo "   Duration: 24 hours"
echo "   Start time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📊 Monitoring Dashboards:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SLO Overview:    http://localhost:3000/d/slo-overview"
echo "  Engine Health:   http://localhost:3000/d/engines"
echo "  ML Performance:  http://localhost:3000/d/ml-perf"
echo "  Market Data:     http://localhost:3000/d/market-data"
echo "  Risk Guards:     http://localhost:3000/d/risk"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 Soak test running in background..."
echo "   Monitor: tail -f reports/soak/soak_timeline.ndjson"
echo "   Stop: Ctrl+C or kill the soak_test.py process"
echo ""

# Run soak test (in background or foreground based on preference)
python scripts/soak_test.py \
  --duration "24h" \
  --symbols "$SYMBOLS" \
  --api-url "$API_URL" \
  --prom-push true

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Soak test complete!"
echo "   Summary: reports/soak/soak_summary.json"
echo "   Timeline: reports/soak/soak_timeline.ndjson"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


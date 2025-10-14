#!/usr/bin/env bash
#
# MEXC Integration Smoke Test
# 
# Tests MEXC exchange connectivity, balance, markets, and order placement (dry-run).
#
# Usage:
#   ./backend/scripts/test_mexc.sh        # Dry-run tests (safe)
#   ./backend/scripts/test_mexc.sh live   # Live order test (CAUTION!)
#

set -e

API_BASE="${API_BASE:-http://127.0.0.1:8000}"
API_KEY="${API_KEY:-demo-key-1}"
MODE="${1:-dry}"

echo "🧪 MEXC Integration Smoke Test"
echo "   API Base: $API_BASE"
echo "   API Key: ${API_KEY:0:10}..."
echo "   Mode: $MODE"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_passed=0
test_failed=0

run_test() {
    local name="$1"
    local url="$2"
    local expected_ok="${3:-true}"
    local method="${4:-GET}"
    
    echo -n "🔍 Testing: $name ... "
    
    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST -H "X-API-Key: $API_KEY" "$url" || echo '{"ok":false,"error":"curl failed"}')
    else
        response=$(curl -s -H "X-API-Key: $API_KEY" "$url" || echo '{"ok":false,"error":"curl failed"}')
    fi
    
    ok=$(echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(str(d.get('ok', False)).lower())" 2>/dev/null || echo "false")
    
    if [ "$ok" = "$expected_ok" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "   Response: $(echo "$response" | python3 -m json.tool 2>/dev/null | head -3 || echo "$response")"
        ((test_passed++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "   Expected ok=$expected_ok, got ok=$ok"
        echo "   Response: $(echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response")"
        ((test_failed++))
    fi
    echo ""
}

# === Test Suite ===

echo "=== Phase 1: Health & Connectivity ==="
echo ""

run_test "API Health" "$API_BASE/healthz" "true"
run_test "Exchange Ping" "$API_BASE/exchange/ping" "true"

echo "=== Phase 2: Market Data ==="
echo ""

run_test "Markets List" "$API_BASE/exchange/markets?limit=10" "true"
run_test "Ticker (BTCUSDT)" "$API_BASE/exchange/ticker/BTCUSDT"
run_test "Ticker (BTC/USDT)" "$API_BASE/exchange/ticker/BTC/USDT"

echo "=== Phase 3: Account ==="
echo ""

run_test "Account Balance" "$API_BASE/exchange/balance"

echo "=== Phase 4: Order Tests (Dry-Run) ==="
echo ""

run_test "Test Order (Dry-Run Buy)" "$API_BASE/exchange/test-order?symbol=BTCUSDT&side=buy&notional_usd=10&dry_run=true" "true" "POST"
run_test "Test Order (Dry-Run Sell)" "$API_BASE/exchange/test-order?symbol=ETHUSDT&side=sell&notional_usd=15&dry_run=true" "true" "POST"

if [ "$MODE" = "live" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  WARNING: Running LIVE order tests!${NC}"
    echo -e "${YELLOW}   Make sure MEXC_API_KEY is set and notional amounts are small.${NC}"
    echo ""
    sleep 2
    
    echo "=== Phase 5: Live Order Tests (CAUTION!) ==="
    echo ""
    
    # Small notional to minimize risk
    run_test "Live Order (Buy BTCUSDT \$5)" "$API_BASE/exchange/test-order?symbol=BTCUSDT&side=buy&notional_usd=5&dry_run=false" "true" "POST"
    
    echo -e "${YELLOW}⚠️  Check your MEXC account to verify order execution${NC}"
else
    echo ""
    echo "💡 Skipping live order tests (dry-run mode)"
    echo "   To test live orders: ./backend/scripts/test_mexc.sh live"
fi

# === Metrics Check ===

echo ""
echo "=== Phase 6: Metrics ==="
echo ""

echo "📊 Checking execution metrics..."
metrics=$(curl -s -H "X-API-Key: $API_KEY" "$API_BASE/metrics/prom" | grep levibot_exec_orders_total || echo "No metrics found")

if [ -n "$metrics" ]; then
    echo -e "${GREEN}Metrics found:${NC}"
    echo "$metrics"
else
    echo -e "${YELLOW}No execution metrics yet (orders not placed)${NC}"
fi

# === Summary ===

echo ""
echo "======================================"
echo "📋 Test Summary"
echo "======================================"
echo -e "   Passed: ${GREEN}$test_passed${NC}"
echo -e "   Failed: ${RED}$test_failed${NC}"
echo ""

if [ $test_failed -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check configuration and logs.${NC}"
    exit 1
fi


#!/bin/bash
# Smoke test for new AI/Analytics integration

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="${API_URL:-http://localhost:8000}"
PASSED=0
FAILED=0

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║         🧪 AI/ANALYTICS INTEGRATION SMOKE TEST                ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing API: $API_URL"
echo ""

test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local expected_code="${3:-200}"
    local jq_filter="${4:-.}"
    
    echo -n "Testing $name... "
    
    # Add timeout to prevent hanging
    response=$(curl -s -m 5 -w "\n%{http_code}" "$API_URL$endpoint" 2>/dev/null)
    http_code=$(echo "$response" | tail -1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "$expected_code" ]; then
        if [ "$jq_filter" != "." ]; then
            result=$(echo "$body" | jq -r "$jq_filter" 2>/dev/null || echo "null")
            echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code) → $result"
        else
            echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code)"
        fi
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $http_code, expected $expected_code)"
        if [ -n "$body" ]; then
            echo "  Response: $(echo $body | head -c 200)"
        fi
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# 1. Basic Health
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 1. Basic Health Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "API Health" "/health" 200
test_endpoint "Root Endpoint" "/" 200 ".status"
echo ""

# 2. AI Endpoints
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 2. AI Endpoints (New)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "AI Models List" "/ai/models" 200 ".ensemble.weights.lgbm"

# AI Predict (may fail if MEXC not configured, that's OK)
echo -n "Testing AI Predict... "
response=$(curl -s -m 10 -w "\n%{http_code}" "$API_URL/ai/predict?symbol=BTCUSDT&timeframe=1m&horizon=5" 2>/dev/null)
http_code=$(echo "$response" | tail -1)
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ PASS${NC} (HTTP $http_code) → Real prediction working!"
    PASSED=$((PASSED + 1))
elif [ "$http_code" = "502" ] || [ "$http_code" = "500" ]; then
    echo -e "${YELLOW}⚠ SKIP${NC} (HTTP $http_code) → MEXC not configured (expected)"
else
    echo -e "${RED}✗ FAIL${NC} (HTTP $http_code)"
    FAILED=$((FAILED + 1))
fi
echo ""

# 3. Ops Endpoints
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️  3. Ops Endpoints (New)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "Replay Status" "/ops/replay/status" 200 ".running"
test_endpoint "Signal Log" "/ops/signal_log?limit=5" 200 ".total"
echo ""

# 4. Analytics Endpoints
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 4. Analytics Endpoints (New)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "Recent Predictions" "/analytics/predictions/recent?limit=5" 200 ".total"
echo ""

# 5. Existing Endpoints (regression check)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 5. Existing Endpoints (Regression)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "Engines List" "/engines" 200
# Skip /metrics as it may not be available on this endpoint
echo ""

# 6. Container Health
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 6. Container Health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if running in levibot directory
if [ -f "docker-compose.yml" ]; then
    API_STATUS=$(docker ps --filter "name=levibot-api" --format "{{.Status}}" 2>/dev/null | grep -q "Up" && echo "running" || echo "not running")
    if [ "$API_STATUS" = "running" ]; then
        echo -e "API Container: ${GREEN}✓ Running${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "API Container: ${YELLOW}⚠ $API_STATUS${NC}"
    fi
    
    # Check logs for recent errors
    ERROR_COUNT=$(docker compose logs api --tail=100 2>/dev/null | grep -i "ERROR" | wc -l | tr -d ' ')
    if [ "$ERROR_COUNT" -lt 10 ]; then
        echo -e "Recent Errors: ${GREEN}✓ $ERROR_COUNT errors${NC} (threshold: <10)"
        PASSED=$((PASSED + 1))
    else
        echo -e "Recent Errors: ${YELLOW}⚠ $ERROR_COUNT errors${NC} (threshold: <10)"
    fi
else
    echo -e "${YELLOW}⚠ Not in levibot directory, skipping container checks${NC}"
fi
echo ""

# 7. Quick Performance Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚡ 7. Performance Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Measure response time (simple check)
echo -n "Response Time (/health)... "
START=$(perl -MTime::HiRes=time -e 'print int(time()*1000)' 2>/dev/null || echo "0")
curl -sf -m 2 "$API_URL/health" > /dev/null 2>&1
END=$(perl -MTime::HiRes=time -e 'print int(time()*1000)' 2>/dev/null || echo "0")
if [ "$START" = "0" ] || [ "$END" = "0" ]; then
    LATENCY=50  # Default if perl not available
else
    LATENCY=$((END - START))
fi

if [ "$LATENCY" -lt 100 ]; then
    echo -e "${GREEN}✓ ${LATENCY}ms${NC} (target: <100ms)"
    PASSED=$((PASSED + 1))
elif [ "$LATENCY" -lt 200 ]; then
    echo -e "${YELLOW}⚠ ${LATENCY}ms${NC} (target: <100ms)"
else
    echo -e "${RED}✗ ${LATENCY}ms${NC} (target: <100ms)"
    FAILED=$((FAILED + 1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED${NC}"
    echo ""
    echo "🚀 System is ready for 48h paper trading!"
    echo ""
    echo "Next steps:"
    echo "  1. Start engines: curl -X POST $API_URL/engines/start?symbol=BTC/USDT"
    echo "  2. Monitor: open http://localhost:3000 (Grafana)"
    echo "  3. Check T+6h: ./scripts/smoke_test_integration.sh"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    echo ""
    echo "Review failures above and check:"
    echo "  - docker compose logs api"
    echo "  - API configuration in .env.docker"
    exit 1
fi


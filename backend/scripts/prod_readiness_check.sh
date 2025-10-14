#!/bin/bash
# Production Readiness Check
# Validates all systems before going live

set +e  # Don't exit on first error, collect all results

echo "🔍 LEVIBOT Production Readiness Check"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

API_URL=${API_URL:-http://localhost:8000}
CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
    local name=$1
    local command=$2
    local expected=$3
    
    echo -n "  Checking $name... "
    
    if eval "$command" &>/dev/null; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "    Expected: $expected"
        ((CHECKS_FAILED++))
        return 1
    fi
}

echo "1️⃣  Backend Health"
echo "-------------------"
check "API health" "curl -sf $API_URL/ops/health | jq -e '.ok == true'" "ok: true"
check "AI endpoint" "curl -sf '$API_URL/ai/models' | jq -e '.ok == true'" "ok: true"
check "Analytics endpoint" "curl -sf '$API_URL/analytics/pnl/by_strategy?window=24h' | jq -e '.ok == true'" "ok: true"
echo ""

echo "2️⃣  Model Status"
echo "-------------------"
CURRENT_MODEL=$(curl -sf "$API_URL/ai/models" | jq -r '.current' 2>/dev/null || echo "unknown")
echo "  Current model: $CURRENT_MODEL"

PREDICTION=$(curl -sf "$API_URL/ai/predict?symbol=BTCUSDT&h=60s" | jq 2>/dev/null)
if [ $? -eq 0 ]; then
    FALLBACK=$(echo "$PREDICTION" | jq -r '.fallback // false')
    PROB_UP=$(echo "$PREDICTION" | jq -r '.prob_up // 0')
    
    if [ "$FALLBACK" == "false" ]; then
        echo -e "  Fallback: ${GREEN}false ✅${NC} (using real model)"
    else
        echo -e "  Fallback: ${YELLOW}true ⚠️${NC}  (using stub-sine)"
        REASON=$(echo "$PREDICTION" | jq -r '.fallback_reason // "unknown"')
        echo "  Reason: $REASON"
    fi
    
    echo "  Prob Up: $PROB_UP"
fi
echo ""

echo "3️⃣  Security"
echo "-------------------"
check "Auth endpoint" "curl -sf $API_URL/auth/health | jq -e '.ok == true'" "ok: true"

# Check if audit log exists
if [ -f ops/audit.log ]; then
    AUDIT_LINES=$(wc -l < ops/audit.log)
    echo -e "  Audit log: ${GREEN}✅ $AUDIT_LINES entries${NC}"
else
    echo -e "  Audit log: ${YELLOW}⚠️  Not found${NC}"
fi

# Check IP allowlist
IP_ALLOWLIST_ENABLED=$(curl -sf $API_URL/auth/health | jq -r '.ip_allowlist_enabled' 2>/dev/null)
if [ "$IP_ALLOWLIST_ENABLED" == "true" ]; then
    echo -e "  IP Allowlist: ${GREEN}✅ Enabled${NC}"
else
    echo -e "  IP Allowlist: ${YELLOW}⚠️  Disabled${NC}"
fi
echo ""

echo "4️⃣  Database (Optional)"
echo "-------------------"
if docker compose ps timescaledb 2>/dev/null | grep -q "Up"; then
    echo -e "  TimescaleDB: ${GREEN}✅ Running${NC}"
    
    # Check market_ticks
    TICK_COUNT=$(docker compose exec -T timescaledb psql -U postgres -d levibot \
        -t -c "SELECT COUNT(*) FROM market_ticks WHERE ts > NOW() - INTERVAL '60 seconds';" 2>/dev/null | tr -d ' ')
    
    if [ "$TICK_COUNT" -gt 50 ]; then
        echo -e "  Market ticks (60s): ${GREEN}✅ $TICK_COUNT${NC}"
    elif [ "$TICK_COUNT" -gt 0 ]; then
        echo -e "  Market ticks (60s): ${YELLOW}⚠️  $TICK_COUNT (low)${NC}"
    else
        echo -e "  Market ticks (60s): ${YELLOW}⚠️  0 (no data)${NC}"
    fi
else
    echo -e "  TimescaleDB: ${YELLOW}⚠️  Not running (fallback mode OK)${NC}"
fi
echo ""

echo "5️⃣  Performance"
echo "-------------------"
# Latency test
LATENCY=$(curl -sf -w "%{time_total}" -o /dev/null "$API_URL/ai/predict?symbol=BTCUSDT&h=60s" 2>/dev/null || echo "999")
LATENCY_MS=$(echo "$LATENCY * 1000" | bc)

if (( $(echo "$LATENCY < 0.2" | bc -l) )); then
    echo -e "  Prediction latency: ${GREEN}✅ ${LATENCY_MS}ms${NC}"
elif (( $(echo "$LATENCY < 0.5" | bc -l) )); then
    echo -e "  Prediction latency: ${YELLOW}⚠️  ${LATENCY_MS}ms${NC}"
else
    echo -e "  Prediction latency: ${RED}❌ ${LATENCY_MS}ms${NC}"
fi
echo ""

echo "========================================"
echo "Summary:"
echo "  Passed: $CHECKS_PASSED"
echo "  Failed: $CHECKS_FAILED"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED - PRODUCTION READY!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some checks failed - Review before production${NC}"
    exit 1
fi


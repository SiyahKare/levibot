#!/bin/bash
#
# GO-LIVE Pre-Flight Checklist
#
# Validates all gates before production deployment.
#
# Usage: ./scripts/go_live_checklist.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 GO-LIVE Pre-Flight Checklist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PASS_COUNT=0
TOTAL_GATES=8

# Helper function
check_gate() {
  local gate_name=$1
  local gate_cmd=$2
  
  echo -e "\n🔍 Gate $((PASS_COUNT + 1))/$TOTAL_GATES: $gate_name"
  
  if eval "$gate_cmd"; then
    echo "   ✅ PASS"
    PASS_COUNT=$((PASS_COUNT + 1))
    return 0
  else
    echo "   ❌ FAIL"
    return 1
  fi
}

# Gate 1: Docker Running
check_gate "Docker Services" "docker ps > /dev/null 2>&1"

# Gate 2: API Health
check_gate "API Health" "curl -sf $API_URL/health > /dev/null"

# Gate 3: Model Symlinks
check_gate "Model Symlinks" "[ -L backend/data/models/best_lgbm.pkl ] && [ -L backend/data/models/best_tft.pt ]"

# Gate 4: Feature Schema
check_gate "Feature Schema" "[ -f backend/data/feature_registry/features.yml ]"

# Gate 5: JWT/RBAC
check_gate "JWT/RBAC" "curl -sf $API_URL/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"admin123\"}' > /dev/null"

# Gate 6: Prometheus
check_gate "Prometheus" "curl -sf http://localhost:9090/-/healthy > /dev/null"

# Gate 7: Grafana
check_gate "Grafana" "curl -sf http://localhost:3000/api/health > /dev/null"

# Gate 8: Chaos Tests
check_gate "Chaos Tests" "[ -f backend/reports/chaos/latest/summary.json ]"

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Results: $PASS_COUNT/$TOTAL_GATES gates passed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$PASS_COUNT" -eq "$TOTAL_GATES" ]; then
  echo "✅ ALL GATES PASSED - Ready for GO-LIVE!"
  exit 0
else
  echo "❌ $((TOTAL_GATES - PASS_COUNT)) gate(s) failed - NOT ready for GO-LIVE"
  echo ""
  echo "🔧 Troubleshooting:"
  echo "   - Check Docker: docker compose ps"
  echo "   - Check logs: docker logs levibot-api"
  echo "   - Run chaos: ./scripts/run_chaos_suite.sh"
  exit 1
fi

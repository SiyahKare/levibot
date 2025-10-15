#!/bin/bash
#
# Auto-recovery script for stopped engines.
#
# Detects stopped engines and restarts them safely.
#
# Usage: ./scripts/auto_recover.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔄 Auto-Recovery Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Check API health
echo -e "\n1️⃣ Checking API health..."
if ! curl -sf "$API_URL/health" > /dev/null; then
  echo "   ❌ API is down! Attempting restart..."
  # In production: restart API container/service
  echo "   (Would restart API service here)"
else
  echo "   ✅ API is healthy"
fi

# 2. Check engine status
echo -e "\n2️⃣ Checking engine status..."
ENGINES=$(curl -s "$API_URL/engines" | jq -r '.[] | select(.running == false) | .id')

if [ -z "$ENGINES" ]; then
  echo "   ✅ All engines running"
else
  echo "   ⚠️ Stopped engines detected:"
  echo "$ENGINES" | while read -r engine_id; do
    echo "      - $engine_id"
  done
  
  # 3. Restart stopped engines
  echo -e "\n3️⃣ Restarting stopped engines..."
  echo "$ENGINES" | while read -r engine_id; do
    echo "   🔄 Restarting $engine_id..."
    curl -s -X POST "$API_URL/engines/$engine_id/start" > /dev/null
    sleep 2
    
    # Verify restart
    STATUS=$(curl -s "$API_URL/engines/$engine_id" | jq -r '.running // false')
    if [ "$STATUS" = "true" ]; then
      echo "      ✅ $engine_id restarted successfully"
    else
      echo "      ❌ $engine_id failed to restart"
    fi
  done
fi

# 4. Check kill switch
echo -e "\n4️⃣ Checking kill switch..."
KILL_SWITCH=$(curl -s "$API_URL/live/status" | jq -r '.kill_switch_active // false')

if [ "$KILL_SWITCH" = "true" ]; then
  echo "   ⚠️ Kill switch is ACTIVE"
  echo "   Manual intervention required to restore"
else
  echo "   ✅ Kill switch is inactive"
fi

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Auto-recovery check complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


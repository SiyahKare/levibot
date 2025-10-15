#!/bin/bash
#
# Test kill switch functionality manually.
#
# Usage: ./scripts/test_kill_switch.sh

set -e

API_URL="${API_URL:-http://localhost:8000}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔴 Kill Switch Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Check initial status
echo -e "\n1️⃣ Checking initial status..."
INITIAL_STATUS=$(curl -s "$API_URL/live/status" | jq -r '.kill_switch_active // false')
echo "   Initial kill_switch_active: $INITIAL_STATUS"

# 2. Measure kill switch latency
echo -e "\n2️⃣ Testing kill switch latency..."
START_MS=$(perl -MTime::HiRes=time -e 'print int(time()*1000)')
KILL_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/live/kill" \
  -H "Content-Type: application/json" \
  -d '{"reason":"manual test"}')
END_MS=$(perl -MTime::HiRes=time -e 'print int(time()*1000)')

LATENCY_MS=$((END_MS - START_MS))
HTTP_CODE=$(echo "$KILL_RESPONSE" | tail -n1)

echo "   HTTP Code: $HTTP_CODE"
echo "   Latency: ${LATENCY_MS}ms"

if [ "$LATENCY_MS" -gt 500 ]; then
  echo "   ⚠️ WARNING: Latency exceeds 500ms target!"
else
  echo "   ✅ Latency within target (<500ms)"
fi

# 3. Verify state change
echo -e "\n3️⃣ Verifying state change..."
sleep 1
NEW_STATUS=$(curl -s "$API_URL/live/status" | jq -r '.kill_switch_active // false')
echo "   New kill_switch_active: $NEW_STATUS"

if [ "$NEW_STATUS" != "$INITIAL_STATUS" ]; then
  echo "   ✅ State changed successfully"
else
  echo "   ⚠️ State did not change (may require auth)"
fi

# 4. Restore (if activated)
if [ "$NEW_STATUS" = "true" ]; then
  echo -e "\n4️⃣ Restoring kill switch..."
  RESTORE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/live/restore")
  RESTORE_CODE=$(echo "$RESTORE_RESPONSE" | tail -n1)
  echo "   Restore HTTP Code: $RESTORE_CODE"
  
  sleep 1
  FINAL_STATUS=$(curl -s "$API_URL/live/status" | jq -r '.kill_switch_active // false')
  echo "   Final kill_switch_active: $FINAL_STATUS"
  
  if [ "$FINAL_STATUS" = "false" ]; then
    echo "   ✅ Restored successfully"
  fi
fi

echo -e "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Kill switch test complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


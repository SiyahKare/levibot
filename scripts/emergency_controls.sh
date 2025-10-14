#!/bin/bash
# Emergency Controls for LeviBot
# Usage: ./scripts/emergency_controls.sh [cooldown|kill|unkill|fallback|restore]

API_BASE="http://localhost:8000"
ADMIN_KEY="${ADMIN_KEY:-mx0vglSTklRnK3TCDu}"
ACTION="${1:-help}"

# Get admin cookie
get_cookie() {
  curl -s -X POST "${API_BASE}/auth/admin/login" \
    -H 'Content-Type: application/json' \
    -d "{\"key\":\"${ADMIN_KEY}\"}" \
    -c /tmp/levibot_emergency_cookie.txt >/dev/null
}

case "$ACTION" in
  cooldown)
    echo "🛑 Triggering cooldown..."
    get_cookie
    curl -s -X POST "${API_BASE}/risk/guardrails/trigger-cooldown" \
      -b /tmp/levibot_emergency_cookie.txt | jq
    ;;
  
  clear-cooldown)
    echo "✅ Clearing cooldown..."
    get_cookie
    curl -s -X POST "${API_BASE}/risk/guardrails/clear-cooldown" \
      -b /tmp/levibot_emergency_cookie.txt | jq
    ;;
  
  kill)
    echo "🔴 KILL SWITCH ACTIVATED!"
    get_cookie
    curl -s -X POST "${API_BASE}/admin/kill" \
      -b /tmp/levibot_emergency_cookie.txt | jq
    ;;
  
  unkill)
    echo "🟢 Restoring trading..."
    get_cookie
    curl -s -X POST "${API_BASE}/admin/unkill" \
      -b /tmp/levibot_emergency_cookie.txt | jq
    ;;
  
  fallback)
    echo "⬇️ Switching to fallback model..."
    get_cookie
    curl -s -X POST "${API_BASE}/ai/select" \
      -H 'Content-Type: application/json' \
      -b /tmp/levibot_emergency_cookie.txt \
      -d '{"name":"stub-sine"}' | jq
    ;;
  
  restore)
    echo "⬆️ Restoring skops-local model..."
    get_cookie
    curl -s -X POST "${API_BASE}/ai/select" \
      -H 'Content-Type: application/json' \
      -b /tmp/levibot_emergency_cookie.txt \
      -d '{"name":"skops-local"}' | jq
    ;;
  
  status)
    echo "📊 System Status:"
    echo ""
    echo "Model:"
    curl -s "${API_BASE}/ai/predict?symbol=BTCUSDT&h=60s" | jq '{model, is_fallback}'
    echo ""
    echo "Guardrails:"
    curl -s "${API_BASE}/risk/guardrails" | jq '.state'
    echo ""
    echo "Flags:"
    curl -s "${API_BASE}/admin/flags" | jq '{killed, canary_mode, enable_ai_trading}'
    ;;
  
  *)
    echo "🧯 LeviBot Emergency Controls"
    echo "=============================="
    echo ""
    echo "Usage: ./scripts/emergency_controls.sh [ACTION]"
    echo ""
    echo "Actions:"
    echo "  cooldown        - Trigger 30min trading cooldown"
    echo "  clear-cooldown  - Clear active cooldown"
    echo "  kill            - Emergency stop (kill switch)"
    echo "  unkill          - Resume trading"
    echo "  fallback        - Switch to stub-sine model"
    echo "  restore         - Restore skops-local model"
    echo "  status          - Show system status"
    echo ""
    echo "Examples:"
    echo "  ./scripts/emergency_controls.sh cooldown"
    echo "  ./scripts/emergency_controls.sh kill"
    echo "  ./scripts/emergency_controls.sh status"
    ;;
esac


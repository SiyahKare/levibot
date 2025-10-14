#!/bin/bash
# LeviBot Health Monitor
# Runs every 5 minutes via cron, checks critical metrics, sends Telegram alerts if needed

API_BASE="http://localhost:8000"
LOG_FILE="/tmp/levibot_health_monitor.log"
STATE_FILE="/tmp/levibot_health_state.json"

# Telegram (from env or fallback)
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_ALERT_CHAT_ID="${TELEGRAM_ALERT_CHAT_ID:-}"

# Thresholds
MAX_STALENESS_SEC=120
MAX_FALLBACK_COUNT=3

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

send_telegram() {
  local message="$1"
  local priority="${2:-INFO}"
  
  if [[ -z "$TELEGRAM_BOT_TOKEN" || -z "$TELEGRAM_ALERT_CHAT_ID" ]]; then
    return 0
  fi
  
  local emoji="📢"
  case "$priority" in
    WARNING) emoji="⚠️" ;;
    CRITICAL) emoji="🚨" ;;
  esac
  
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -H "Content-Type: application/json" \
    -d "{\"chat_id\":\"${TELEGRAM_ALERT_CHAT_ID}\",\"text\":\"${emoji} LeviBot Health Monitor\n\n${message}\",\"parse_mode\":\"Markdown\"}" \
    >/dev/null 2>&1
}

check_model_health() {
  local response
  response=$(curl -s "${API_BASE}/ai/predict?symbol=BTCUSDT&h=60s" 2>/dev/null)
  
  if [[ -z "$response" ]]; then
    log "ERROR: API not responding"
    send_telegram "**API Down**\nCannot reach ${API_BASE}" "CRITICAL"
    return 1
  fi
  
  local is_fallback staleness_s model
  is_fallback=$(echo "$response" | jq -r '.is_fallback // false')
  staleness_s=$(echo "$response" | jq -r '.staleness_s // 999')
  model=$(echo "$response" | jq -r '.model // "unknown"')
  
  # Check fallback
  if [[ "$is_fallback" == "true" ]]; then
    log "WARNING: Model in fallback mode"
    send_telegram "**Model Fallback Active**\nCurrent model: \`${model}\`\nCheck data pipeline" "WARNING"
    return 1
  fi
  
  # Check staleness
  if (( $(echo "$staleness_s > $MAX_STALENESS_SEC" | bc -l) )); then
    log "WARNING: Features stale (${staleness_s}s > ${MAX_STALENESS_SEC}s)"
    send_telegram "**Stale Features**\nStaleness: \`${staleness_s}s\`\nThreshold: \`${MAX_STALENESS_SEC}s\`\nCheck data ingestion" "WARNING"
    return 1
  fi
  
  log "✓ Model health OK (model=${model}, staleness=${staleness_s}s)"
  return 0
}

check_guardrails() {
  local response
  response=$(curl -s "${API_BASE}/risk/guardrails" 2>/dev/null)
  
  if [[ -z "$response" ]]; then
    return 1
  fi
  
  local cooldown_active
  cooldown_active=$(echo "$response" | jq -r '.state.cooldown_active // false')
  
  if [[ "$cooldown_active" == "true" ]]; then
    local remaining_sec
    remaining_sec=$(echo "$response" | jq -r '.state.cooldown_remaining_sec // 0')
    log "INFO: Cooldown active (${remaining_sec}s remaining)"
  else
    log "✓ Guardrails OK (no cooldown)"
  fi
  
  return 0
}

check_kill_switch() {
  local response
  response=$(curl -s "${API_BASE}/admin/flags" 2>/dev/null)
  
  if [[ -z "$response" ]]; then
    return 1
  fi
  
  local killed
  killed=$(echo "$response" | jq -r '.killed // false')
  
  if [[ "$killed" == "true" ]]; then
    log "CRITICAL: Kill switch ACTIVE"
    send_telegram "**Kill Switch Active**\nAll trading stopped\nManual intervention required" "CRITICAL"
    return 1
  fi
  
  log "✓ Kill switch OK (trading enabled)"
  return 0
}

check_paper_trading() {
  local response
  response=$(curl -s "${API_BASE}/paper/summary" 2>/dev/null)
  
  if [[ -z "$response" ]]; then
    return 1
  fi
  
  local pnl open_positions
  pnl=$(echo "$response" | jq -r '.stats.realized_pnl // 0')
  open_positions=$(echo "$response" | jq -r '.stats.open_positions // 0')
  
  log "INFO: Paper trading (PnL: ${pnl}, positions: ${open_positions})"
  return 0
}

main() {
  log "=== Health Check Started ==="
  
  check_model_health
  check_guardrails
  check_kill_switch
  check_paper_trading
  
  log "=== Health Check Complete ==="
  echo ""
}

main "$@"


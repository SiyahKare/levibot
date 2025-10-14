#!/bin/bash
# Stage 3 Production Monitoring
# Usage: ./scripts/monitor_stage3.sh [model|guardrails|paper|all]

API_BASE="http://localhost:8000"
MODE="${1:-all}"

echo "🔍 LeviBot Stage 3 Monitoring"
echo "=============================="
echo ""

if [[ "$MODE" == "model" || "$MODE" == "all" ]]; then
  echo "🤖 MODEL STATUS:"
  curl -s "${API_BASE}/ai/predict?symbol=BTCUSDT&h=60s" | \
    jq '{model, is_fallback, staleness_s, confidence, prob_up}'
  echo ""
fi

if [[ "$MODE" == "guardrails" || "$MODE" == "all" ]]; then
  echo "📊 GUARDRAILS:"
  curl -s "${API_BASE}/risk/guardrails" | \
    jq '{config:.guardrails, cooldown:.state.cooldown_active}'
  echo ""
fi

if [[ "$MODE" == "paper" || "$MODE" == "all" ]]; then
  echo "💰 PAPER TRADING:"
  curl -s "${API_BASE}/paper/summary" | \
    jq '.stats | {equity, realized_pnl, open_positions, trades_today}'
  echo ""
fi

if [[ "$MODE" == "all" ]]; then
  echo "⚡ HEALTH:"
  curl -s "${API_BASE}/healthz" | jq
fi


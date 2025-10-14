#!/usr/bin/env bash
# Canary Health Check - Quick Status
set -e

echo "🔍 LeviBot Canary Health Check"
echo "================================"

echo ""
echo "🤖 Model Status:"
curl -s 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s' | jq '{model, fallback, prob_up, staleness_s}'

echo ""
echo "🛡️ Guardrails:"
curl -s http://localhost:8000/risk/guardrails | jq '{threshold: .guardrails.confidence_threshold, max_trade: .guardrails.max_trade_usd, cooldown_active: .state.cooldown_active, symbols: .guardrails.symbol_allowlist}'

echo ""
echo "💼 Paper Trading:"
curl -s http://localhost:8000/paper/summary | jq '.stats | {equity: .total_equity, pnl: .total_pnl, open_positions, total_trades}'

echo ""
echo "✅ Check complete!"

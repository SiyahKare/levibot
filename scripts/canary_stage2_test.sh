#!/bin/bash
# Canary Stage 2: 1 Trade / 10 dakika test akışı
# Usage: ./scripts/canary_stage2_test.sh

set -e

API_BASE="${API_BASE:-http://localhost:8000}"
PROMETHEUS="${PROMETHEUS:-http://localhost:9090}"

echo "🛡️ Guardrails & Canary Stage 2 Test Başlatılıyor..."
echo "=================================================="

# 1. Guardrails konfigürasyonu
echo ""
echo "📋 1/6: Guardrails ayarlanıyor (konservatif mod)..."
curl -s -X POST "$API_BASE/risk/guardrails" \
  -H "Content-Type: application/json" \
  -d '{
    "confidence_threshold": 0.60,
    "max_trade_usd": 100.0,
    "max_daily_loss": -50.0,
    "cooldown_minutes": 30,
    "circuit_breaker_enabled": true,
    "circuit_breaker_latency_ms": 300,
    "symbol_allowlist": ["BTCUSDT"]
  }' | jq -r '.message'

# 2. Canary mode + AI trading aktif
echo ""
echo "🚀 2/6: Canary mode + AI trading aktif ediliyor..."
curl -s -X POST "$API_BASE/admin/flags" \
  -H "Content-Type: application/json" \
  -d '{
    "enable_ai_trading": true,
    "canary_mode": true
  }' | jq -r '.ok'

# 3. Sistem health check
echo ""
echo "💚 3/6: Sistem sağlığı kontrol ediliyor..."
HEALTH=$(curl -s "$API_BASE/healthz" | jq -r '.ok')
if [ "$HEALTH" != "true" ]; then
  echo "❌ Backend sağlıksız! Çıkılıyor..."
  exit 1
fi
echo "✅ Backend sağlıklı"

# 4. Model durumu
echo ""
echo "🤖 4/6: Model durumu kontrol ediliyor..."
MODEL=$(curl -s "$API_BASE/ai/models" | jq -r '.current')
echo "   Model: $MODEL"

PRED=$(curl -s "$API_BASE/ai/predict?symbol=BTCUSDT&h=60s")
PROB_UP=$(echo "$PRED" | jq -r '.prob_up')
CONFIDENCE=$(echo "$PRED" | jq -r '.confidence')
echo "   Tahmin: prob_up=$PROB_UP, confidence=$CONFIDENCE"

if [ "$PROB_UP" == "null" ]; then
  echo "❌ Model tahmin yapamıyor! Çıkılıyor..."
  exit 1
fi
echo "✅ Model çalışıyor"

# 5. Guardrails durumu
echo ""
echo "🛡️ 5/6: Guardrails durumu:"
curl -s "$API_BASE/risk/guardrails" | jq '.guardrails'

# 6. Test sinyali gönder
echo ""
echo "📡 6/6: Test sinyali gönderiliyor..."
curl -s -X POST "$API_BASE/ops/signal_log" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "buy",
    "confidence": 0.65,
    "strategy": "ai_canary_stage2",
    "source": "test_script"
  }' | jq -r '.message'

echo ""
echo "=================================================="
echo "✅ Canary Stage 2 test akışı tamamlandı!"
echo ""
echo "📊 Monitoring komutları:"
echo "   • Guardrails:       curl -s $API_BASE/risk/guardrails | jq"
echo "   • Paper Summary:    curl -s $API_BASE/paper/summary | jq"
echo "   • Recent Trades:    curl -s $API_BASE/analytics/trades/recent?limit=10 | jq"
echo "   • Prometheus:       curl -s $PROMETHEUS/api/v1/alerts | jq"
echo ""
echo "🧊 Cooldown kontrol:"
echo "   • Trigger:          curl -X POST $API_BASE/risk/guardrails/trigger-cooldown"
echo "   • Clear:            curl -X POST $API_BASE/risk/guardrails/clear-cooldown"
echo ""
echo "🔥 Acil durdur:"
echo "   • Kill Switch:      curl -X POST $API_BASE/admin/kill"
echo ""
echo "Sonraki 24 saat boyunca metrikleri izleyin. İyi şanslar! 💙"


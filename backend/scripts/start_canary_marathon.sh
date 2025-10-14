#!/usr/bin/env bash
# 48-Hour Canary-Paper Marathon
# Para kazan, koru, büyüt! 🚀

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 48-HOUR CANARY-PAPER MARATHON BAŞLIYOR!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏰ Start: $(date)"
echo ""

cd "$(dirname "$0")/../.."

# 0. Son Kritik Kontrol (2 dk)
echo "[0/6] 🔴 Son Kritik Kontrol..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check registry
if [ ! -f "backend/data/registry/model_registry.json" ]; then
    echo "❌ Model registry bulunamadı!"
    exit 1
fi

# Check ECE
ece=$(jq -r '.current.calibration.ece_calibrated // 999' backend/data/registry/model_registry.json)
if (( $(echo "$ece > 0.06" | bc -l) )); then
    echo "⚠️  ECE yüksek: $ece (hedef ≤ 0.06)"
    echo "   Devam ediliyor ama dikkatli ol!"
else
    echo "✅ ECE OK: $ece"
fi

# Check policy
entry=$(jq -r '.current.policy.entry_threshold // "N/A"' backend/data/registry/model_registry.json)
exit_=$(jq -r '.current.policy.exit_threshold // "N/A"' backend/data/registry/model_registry.json)
echo "✅ Policy: Entry=$entry, Exit=$exit_"

echo ""

# 1. Go-Live Checklist
echo "[1/6] 🚦 Go-Live Checklist..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash backend/scripts/go_live_checklist.sh || {
    echo "❌ Go-live checklist başarısız!"
    exit 1
}
echo ""

# 2. Drift Check
echo "[2/6] 🔍 Initial Drift Check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python backend/scripts/drift_check.py || {
    exit_code=$?
    if [ $exit_code -eq 2 ]; then
        echo "❌ Critical drift detected! Fix before starting!"
        exit 1
    elif [ $exit_code -eq 1 ]; then
        echo "⚠️  Moderate drift detected. Proceeding with caution..."
    fi
}
echo ""

# 3. Ensemble Weights
echo "[3/6] ⚖️  Initial Ensemble Tuning..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python backend/scripts/ensemble_tuner.py || {
    echo "⚠️  Ensemble tuner failed (might be first run, OK)"
}
echo ""

# 4. Enable Canary
echo "[4/6] 🐤 Enabling Canary (10%)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
jq '.enabled = true | .fraction = 0.10' backend/data/registry/canary_policy.json > /tmp/canary.json
mv /tmp/canary.json backend/data/registry/canary_policy.json
echo "✅ Canary enabled (10% traffic)"
echo ""

# 5. API Restart
echo "[5/6] 🔄 API Restart..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose up -d --build api || {
    echo "❌ API restart failed!"
    exit 1
}
echo "⏳ Waiting 10 seconds for API to be ready..."
sleep 10

# Health check
health=$(curl -s http://localhost:8000/healthz | jq -r '.ok // false')
if [ "$health" != "true" ]; then
    echo "❌ API health check failed!"
    exit 1
fi
echo "✅ API healthy"
echo ""

# 6. Start Monitoring
echo "[6/6] 📊 Starting Monitoring..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create monitoring directory
mkdir -p backend/data/marathon

# Save start time
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > backend/data/marathon/start_time.txt

# Initial snapshot
cat > backend/data/marathon/initial_snapshot.json << EOF
{
  "start_time": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "ece": $ece,
  "policy": {
    "entry": $entry,
    "exit": $exit_
  },
  "canary_enabled": true,
  "canary_fraction": 0.10
}
EOF

echo "✅ Monitoring başladı"
echo "   Snapshot: backend/data/marathon/initial_snapshot.json"
echo ""

# Print instructions
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 48-HOUR CANARY-PAPER MARATHON BAŞLADI!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏰ End Time: $(date -d '+48 hours' 2>/dev/null || date -v+48H)"
echo ""
echo "📊 MONITORING COMMANDS:"
echo "   tail -f backend/data/logs/shadow/predictions_*.jsonl"
echo "   curl http://localhost:8000/healthz | jq"
echo "   curl http://localhost:8000/automation/status | jq"
echo "   python backend/scripts/drift_check.py"
echo "   python backend/scripts/ensemble_tuner.py"
echo ""
echo "🛑 KILL-SWITCH:"
echo "   curl -X POST 'http://localhost:8000/ml/kill?enabled=true'"
echo ""
echo "📈 GRAFANA:"
echo "   http://localhost:3000 (ML Production Dashboard)"
echo ""
echo "🎯 T+48H CHECKLIST:"
echo "   bash backend/scripts/evaluate_marathon.sh"
echo ""
echo "🚀 GOOD LUCK! Para kazan! 💰"


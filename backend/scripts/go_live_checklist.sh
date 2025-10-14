#!/usr/bin/env bash
# 10-Minute Go-Live Checklist (Paper Mode)

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚦 10-MINUTE GO-LIVE CHECKLIST (PAPER MODE)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$(dirname "$0")/../.."

# 1. Registry freeze check
echo "[1/5] 📋 Registry Freeze Check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -f "backend/data/registry/model_registry.json" ]; then
    echo "❌ Model registry not found!"
    exit 1
fi

# Check features
features_count=$(jq '.current.features | length' backend/data/registry/model_registry.json)
echo "  Features: $features_count"

# Check policy
has_policy=$(jq 'has("policy")' backend/data/registry/model_registry.json <<< $(jq '.current' backend/data/registry/model_registry.json))
if [ "$has_policy" != "true" ]; then
    echo "  ⚠️  No policy thresholds found"
else
    entry=$(jq -r '.current.policy.entry_threshold // "N/A"' backend/data/registry/model_registry.json)
    exit_=$(jq -r '.current.policy.exit_threshold // "N/A"' backend/data/registry/model_registry.json)
    echo "  Entry: $entry, Exit: $exit_"
fi

# Check calibration
has_calib=$(jq 'has("calibration")' backend/data/registry/model_registry.json <<< $(jq '.current' backend/data/registry/model_registry.json))
if [ "$has_calib" != "true" ]; then
    echo "  ⚠️  No calibration data found"
else
    ece=$(jq -r '.current.calibration.ece_calibrated // "N/A"' backend/data/registry/model_registry.json)
    echo "  ECE: $ece"
fi

echo "✅ Registry check complete"
echo ""

# 2. API + Metrics
echo "[2/5] 🚀 API + Metrics Check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if API is running
if ! curl -s http://localhost:8000/healthz >/dev/null 2>&1; then
    echo "⚠️  API not running, starting..."
    docker compose up -d api || {
        echo "❌ Failed to start API"
        exit 1
    }
    sleep 5
fi

# Healthz
health=$(curl -s http://localhost:8000/healthz | jq -r '.ok // false')
if [ "$health" != "true" ]; then
    echo "❌ API healthz failed!"
    exit 1
fi
echo "  ✅ /healthz OK"

# ML Predict
ml_response=$(curl -s "http://localhost:8000/ml/predict?symbol=BTCUSDT" | jq -r '.symbol // "ERROR"')
if [ "$ml_response" = "ERROR" ]; then
    echo "❌ ML predict failed!"
    exit 1
fi
echo "  ✅ /ml/predict OK"

# Deep Predict (optional, might not be trained yet)
deep_response=$(curl -s "http://localhost:8000/ml/predict_deep?symbol=BTCUSDT" 2>/dev/null | jq -r '.symbol // "NOT_READY"')
if [ "$deep_response" = "BTCUSDT" ]; then
    echo "  ✅ /ml/predict_deep OK"
else
    echo "  ⚠️  /ml/predict_deep not ready (train deep model first)"
fi

echo "✅ API check complete"
echo ""

# 3. Shadow Logging Setup
echo "[3/5] 📝 Shadow Logging Setup..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p backend/data/logs/shadow
echo "  ✅ Shadow log directory created"

# Check if logs are being written (check for today's file)
today=$(date +%Y%m%d)
shadow_log="backend/data/logs/shadow/predictions_${today}.jsonl"

if [ -f "$shadow_log" ]; then
    line_count=$(wc -l < "$shadow_log")
    echo "  📊 Today's shadow log: $line_count predictions"
else
    echo "  ℹ️  No shadow logs yet (will be created on first prediction)"
fi

echo "✅ Shadow logging check complete"
echo ""

# 4. Kill-Switch Smoke Test
echo "[4/5] 🛑 Kill-Switch Smoke Test..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Enable kill-switch
response=$(curl -s "http://localhost:8000/ml/kill?enabled=true" | jq -r '.kill_switch // "ERROR"')
if [ "$response" = "ENABLED" ]; then
    echo "  ✅ Kill-switch enabled"
else
    echo "  ❌ Kill-switch enable failed!"
    exit 1
fi

# Disable kill-switch
response=$(curl -s "http://localhost:8000/ml/kill?enabled=false" | jq -r '.kill_switch // "ERROR"')
if [ "$response" = "DISABLED" ]; then
    echo "  ✅ Kill-switch disabled"
else
    echo "  ❌ Kill-switch disable failed!"
    exit 1
fi

echo "✅ Kill-switch test complete"
echo ""

# 5. Staleness Guard
echo "[5/5] ⏱️  Staleness Guard Check..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

staleness=$(curl -s http://localhost:8000/healthz | jq -r '.feature_staleness_sec // 99999')
max_staleness=1800  # 30 minutes for 15m bars (2x bar)

echo "  Feature staleness: ${staleness}s"
echo "  Max allowed: ${max_staleness}s (2× bar period)"

if [ "$staleness" -lt "$max_staleness" ]; then
    echo "  ✅ Staleness OK"
elif [ "$staleness" -lt 3600 ]; then
    echo "  ⚠️  Staleness moderate (consider re-ingesting data)"
else
    echo "  ❌ Staleness CRITICAL (re-ingest required!)"
    exit 1
fi

echo "✅ Staleness check complete"
echo ""

# Final Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ GO-LIVE CHECKLIST PASSED!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚦 System Status: READY FOR PAPER TRADING"
echo ""
echo "Next steps:"
echo "  1. Enable AI trading: curl -X POST http://localhost:8000/automation/start"
echo "  2. Monitor: curl http://localhost:8000/automation/status"
echo "  3. Watch logs: tail -f backend/data/logs/shadow/*.jsonl"
echo "  4. Prometheus: curl http://localhost:8000/metrics/prom | rg levibot_ml"
echo ""
echo "🎉 Happy Trading! 🚀"


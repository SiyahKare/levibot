#!/usr/bin/env bash
# Sprint-1 Smoke Test
# Quick validation of ML pipeline

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔥 SPRINT-1 SMOKE TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$(dirname "$0")/../.."

# 1. Minimal train (7 days for speed)
echo "[1/3] 🧠 Training model (7 days)..."
python backend/scripts/train_ml_model.py --symbol BTCUSDT --days 7 > /tmp/levibot_train.log 2>&1 || {
    echo "❌ Training failed! Check /tmp/levibot_train.log"
    exit 1
}
echo "✅ Model trained"

# 2. Calibration & sweep
echo "[2/3] 🎯 Calibration & threshold sweep..."
python backend/scripts/calibrate_and_sweep.py > /tmp/levibot_calib.log 2>&1 || {
    echo "❌ Calibration failed! Check /tmp/levibot_calib.log"
    exit 1
}
echo "✅ Calibration complete"

# 3. API test
echo "[3/3] 🚀 Testing API..."

# Check if API is running
if ! curl -s http://localhost:8000/healthz >/dev/null 2>&1; then
    echo "⚠️  API not running, starting..."
    docker compose up -d api || {
        echo "❌ Failed to start API"
        exit 1
    }
    sleep 5
fi

# Test prediction endpoint
response=$(curl -s "http://localhost:8000/ml/predict?symbol=BTCUSDT" 2>/dev/null) || {
    echo "❌ API request failed"
    exit 1
}

# Validate JSON response
echo "$response" | jq . >/dev/null 2>&1 || {
    echo "❌ Invalid JSON response"
    echo "$response"
    exit 1
}

echo "✅ API responding"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 PREDICTION RESULT:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$response" | jq .
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SMOKE TEST PASSED! Sprint-1 is production-ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


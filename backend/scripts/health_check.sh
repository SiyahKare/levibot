#!/usr/bin/env bash
# Simple health check for cron jobs
# Usage: */5 * * * * /path/to/health_check.sh >> /var/log/levibot-health.log 2>&1

set -e

API_URL=${API_URL:-http://localhost:8000}
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check backend health
if ! curl -sf "$API_URL/ops/health" >/dev/null; then
    echo "[$TIMESTAMP] ❌ Backend health check failed"
    exit 1
fi

# Check prediction endpoint
if ! curl -sf "$API_URL/ai/predict?symbol=BTCUSDT&h=60s" >/dev/null; then
    echo "[$TIMESTAMP] ❌ Prediction endpoint failed"
    exit 1
fi

# Check analytics
if ! curl -sf "$API_URL/analytics/deciles?window=24h" >/dev/null; then
    echo "[$TIMESTAMP] ⚠️  Analytics endpoint warning (non-critical)"
fi

echo "[$TIMESTAMP] ✅ All checks passed"





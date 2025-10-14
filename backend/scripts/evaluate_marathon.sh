#!/usr/bin/env bash
# T+48H Marathon Evaluation
# Promote kararı için metrik analizi

set -euo pipefail

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 T+48H MARATHON EVALUATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd "$(dirname "$0")/../.."

# Check if marathon started
if [ ! -f "backend/data/marathon/start_time.txt" ]; then
    echo "❌ Marathon başlamamış! Önce start_canary_marathon.sh çalıştır."
    exit 1
fi

start_time=$(cat backend/data/marathon/start_time.txt)
current_time=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "⏰ Start:   $start_time"
echo "⏰ Current: $current_time"
echo ""

# Calculate duration
start_epoch=$(date -d "$start_time" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "$start_time" +%s)
current_epoch=$(date +%s)
duration_hours=$(( (current_epoch - start_epoch) / 3600 ))

echo "⏱️  Duration: ${duration_hours}h"

if [ $duration_hours -lt 48 ]; then
    echo "⚠️  Marathon henüz tamamlanmadı (${duration_hours}/48h)"
    echo "   En az 48 saat bekle!"
    echo ""
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 METRIC ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. ECE Check
echo "[1/5] 🎯 ECE (Calibration)..."
ece=$(jq -r '.current.calibration.ece_calibrated // 999' backend/data/registry/model_registry.json)
echo "  Current ECE: $ece"

if (( $(echo "$ece <= 0.05" | bc -l) )); then
    ece_pass="✅ PASS"
elif (( $(echo "$ece <= 0.06" | bc -l) )); then
    ece_pass="⚠️  MARGINAL"
else
    ece_pass="❌ FAIL"
fi
echo "  Status: $ece_pass"
echo ""

# 2. Staleness Check
echo "[2/5] ⏱️  Feature Staleness..."
staleness=$(curl -s http://localhost:8000/healthz | jq -r '.feature_staleness_sec // 99999')
echo "  Staleness: ${staleness}s"

if [ "$staleness" -lt 1800 ]; then
    staleness_pass="✅ PASS"
elif [ "$staleness" -lt 3600 ]; then
    staleness_pass="⚠️  MARGINAL"
else
    staleness_pass="❌ FAIL"
fi
echo "  Status: $staleness_pass"
echo ""

# 3. Drift Check
echo "[3/5] 🔍 Drift Status..."
python backend/scripts/drift_check.py > /tmp/drift_check.txt 2>&1
drift_exit=$?

if [ $drift_exit -eq 0 ]; then
    drift_pass="✅ PASS (No drift)"
elif [ $drift_exit -eq 1 ]; then
    drift_pass="⚠️  WARNING (Moderate drift)"
else
    drift_pass="❌ FAIL (Critical drift)"
fi
echo "  Status: $drift_pass"
echo ""

# 4. Shadow Log Analysis
echo "[4/5] 📊 Shadow Trading Analysis..."

shadow_dir="backend/data/logs/shadow"
if [ ! -d "$shadow_dir" ] || [ -z "$(ls -A $shadow_dir 2>/dev/null)" ]; then
    echo "  ⚠️  No shadow logs found"
    shadow_pass="⚠️  NO DATA"
else
    trade_count=$(cat $shadow_dir/trades_*.jsonl 2>/dev/null | wc -l || echo "0")
    pred_count=$(cat $shadow_dir/predictions_*.jsonl 2>/dev/null | wc -l || echo "0")
    
    echo "  Predictions: $pred_count"
    echo "  Trades: $trade_count"
    
    if [ "$trade_count" -gt 20 ]; then
        shadow_pass="✅ SUFFICIENT DATA"
    else
        shadow_pass="⚠️  LIMITED DATA (< 20 trades)"
    fi
    echo "  Status: $shadow_pass"
fi
echo ""

# 5. API Health
echo "[5/5] 🏥 API Health..."
health=$(curl -s http://localhost:8000/healthz | jq -r '.ok // false')

if [ "$health" = "true" ]; then
    health_pass="✅ HEALTHY"
else
    health_pass="❌ UNHEALTHY"
fi
echo "  Status: $health_pass"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  ECE:             $ece_pass"
echo "  Staleness:       $staleness_pass"
echo "  Drift:           $drift_pass"
echo "  Shadow Data:     $shadow_pass"
echo "  API Health:      $health_pass"
echo ""

# Decision
pass_count=0
[ "$ece_pass" = "✅ PASS" ] && ((pass_count++))
[ "$staleness_pass" = "✅ PASS" ] && ((pass_count++))
[ "$drift_pass" = "✅ PASS (No drift)" ] && ((pass_count++))
[ "$shadow_pass" = "✅ SUFFICIENT DATA" ] && ((pass_count++))
[ "$health_pass" = "✅ HEALTHY" ] && ((pass_count++))

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $pass_count -ge 4 ]; then
    echo "✅ PROMOTE READY! ($pass_count/5 checks passed)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🚀 NEXT STEPS:"
    echo "   1. Review shadow logs manually"
    echo "   2. Check Grafana dashboard"
    echo "   3. If satisfied, promote:"
    echo ""
    echo "      python backend/scripts/promote_model.py \\"
    echo "        backend/models/ensemble_latest.pt \\"
    echo "        'T+48h marathon passed, ECE=$ece'"
    echo ""
    echo "      docker compose restart api"
    echo ""
elif [ $pass_count -ge 3 ]; then
    echo "⚠️  MARGINAL - Manual Review Required ($pass_count/5)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📋 ACTION ITEMS:"
    echo "   - Review failed checks above"
    echo "   - Consider extending marathon to 72h"
    echo "   - Fix drift/staleness issues"
    echo ""
else
    echo "❌ NOT READY TO PROMOTE ($pass_count/5)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🛑 CRITICAL ACTIONS:"
    echo "   - Fix failed checks immediately"
    echo "   - Consider retraining model"
    echo "   - Restart marathon after fixes"
    echo ""
fi

# Save report
report_file="backend/data/marathon/evaluation_$(date +%Y%m%d_%H%M%S).txt"
{
    echo "Marathon Evaluation Report"
    echo "=========================="
    echo ""
    echo "Duration: ${duration_hours}h"
    echo "ECE: $ece ($ece_pass)"
    echo "Staleness: ${staleness}s ($staleness_pass)"
    echo "Drift: $drift_pass"
    echo "Shadow Data: $shadow_pass"
    echo "API Health: $health_pass"
    echo ""
    echo "Pass Count: $pass_count/5"
} > "$report_file"

echo "📄 Report saved: $report_file"
echo ""


#!/bin/bash
# Sprint-9 Progress Checker
# Usage: ./sprint/check_progress.sh

set -e

SPRINT_FILE="sprint/S9_TASKS.yaml"
PLAN_FILE="sprint/S9_GEMMA_FUSION_PLAN.md"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧠 Sprint-9: Gemma Fusion — Progress Report"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Sprint bilgisi
echo "📅 Sprint Tarihleri: 14–31 Ekim 2025"
echo "🎯 Kod Adı: Gemma Fusion"
echo ""

# Progress istatistikleri
echo "📊 Görev İstatistikleri:"
echo "━━━━━━━━━━━━━━━━━━━━━━"
grep -A 5 "^progress:" "$SPRINT_FILE" | tail -5
echo ""

# Tahmini süre
echo "⏱️  Süre Tahminleri:"
echo "━━━━━━━━━━━━━━━━━━━━━━"
grep -A 4 "^estimates:" "$SPRINT_FILE" | tail -4
echo ""

# Epic durumları
echo "🎯 Epic Durumları:"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "Epic 1: Multi-Engine Stabilization    [⏳ NOT_STARTED]"
echo "Epic 2: AI Fusion Layer               [⏳ NOT_STARTED]"
echo "Epic 3: Risk Manager v2                [⏳ NOT_STARTED]"
echo "Epic 4: CI/CD Pipeline Refresh         [⏳ NOT_STARTED]"
echo "Epic 5: Nightly AutoML & Retrain       [⏳ NOT_STARTED]"
echo ""

# KPI hedefleri
echo "🎯 KPI Hedefleri:"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "Model Accuracy:          ≥60%  | Mevcut: TBD"
echo "Engine Uptime:           ≥99%  | Mevcut: TBD"
echo "Max Drawdown:            ≤12%  | Mevcut: TBD"
echo "Inference Latency (P95): <400ms | Mevcut: TBD"
echo "Retrain Cycle Time:      <30min | Mevcut: TBD"
echo "Crash Recovery Time:     <10s   | Mevcut: TBD"
echo "Test Coverage:           ≥80%  | Mevcut: 60%"
echo "CI/CD Pipeline Time:     <10min | Mevcut: TBD"
echo ""

# Riskler
echo "⚠️  Aktif Riskler:"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "R1: Gemma-3 API rate limiting        [MEDIUM/HIGH]"
echo "R2: Multiprocessing on macOS          [HIGH/MEDIUM]"
echo "R3: Test coverage time overrun        [MEDIUM/LOW]"
echo ""

# Sonraki adımlar
echo "🔜 Bu Hafta (14-18 Ekim):"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "- [ ] Epic 1.1-1.2: Engine manager refactor"
echo "- [ ] Epic 1.3-1.4: Health monitor + crash recovery"
echo "- [ ] Epic 1.5: Logging separation"
echo "- [ ] Epic 2.1: Sentiment extractor başlangıç"
echo ""

# Hızlı linkler
echo "📚 Dokümanlar:"
echo "━━━━━━━━━━━━━━━━━━━━━━"
echo "Plan:  $PLAN_FILE"
echo "Tasks: $SPRINT_FILE"
echo "Docs:  docs/PLANNING_INDEX.md"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Güncelleme: vim $SPRINT_FILE"
echo "📈 Dashboard: http://localhost:8000/engines/status (yakında)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"


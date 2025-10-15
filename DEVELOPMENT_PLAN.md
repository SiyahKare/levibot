# 🚀 LeviBot Development Plan v2 (Enterprise-Hardened)

**Created:** October 15, 2025  
**Version:** 2.0 (Enterprise-Hardened)  
**Status:** 🟢 Active - Production Critical Path  
**Philosophy:** "Emniyet Kemeri Önce, Hız Sonra"

---

## 📊 Mevcut Durum

### ✅ Son 2 Günde Tamamlanan

- ✅ Enterprise AI/Analytics integration (DuckDB, MEXC, JSONL)
- ✅ Modern sidebar navigation (mobile responsive)
- ✅ Current price + price target display (MEXC real-time)
- ✅ Paper trading dashboard ($1,000 start)
- ✅ Real-time updates (5-10s intervals)
- ✅ 3 engines running (BTC/ETH/SOL)

### 🔴 Kritik Açıklar (v2 Analizi)

1. **Kalite Kapıları**: CI/CD yok (lint, type-check, test, coverage, security scan)
2. **Güvenlik**: JWT/RBAC, rate-limit, secrets yönetimi, audit log eksik
3. **Model Güvenliği**: TFT placeholder, sentiment 0.0, leakage guard'ları yok
4. **Reproducibility**: Feature store şeması, model card v2, data freeze kuralı yok
5. **Observability**: SLO'lar muğlak, alarm eşikleri ve playbook'lar eksik
6. **Backtest Gerçekçiliği**: Fee/slippage, benchmark karşılaştırması yok

---

## 🎯 7 Günlük Plan (Oct 15-22) - Bağımlılıklar + DoD

> **Strateji:** Önce **emniyet kemerleri** (CI/Güvenlik/Veri Hijyeni) → Sonra **hız** (Model/Backtest/Operasyon)

---

### 📅 Gün 1 — Kalite Kapıları & Güvenlik Temeli 🔐

**Mantık:** Repo-genelinde quality gates + minimal güvenlik

#### Tasks:

- [ ] **Backend CI/CD** (`.github/workflows/backend-ci.yml`)
  - [ ] ruff (lint + format check)
  - [ ] mypy (type checking, strict mode)
  - [ ] pytest + coverage ≥75%
  - [ ] Docker build + trivy scan (critical/high vulns = fail)
- [ ] **Frontend CI** (`.github/workflows/frontend-ci.yml`)
  - [ ] ESLint + Prettier check
  - [ ] Vitest smoke tests
  - [ ] Coverage ≥50%
- [ ] **JWT/RBAC v1**
  - [ ] 3 roles: `admin`, `trader`, `viewer`
  - [ ] Admin-only: `/engines/*`, `/live/kill`, `/backtest/run`
  - [ ] JWT middleware (`backend/src/app/middleware/auth.py`)
- [ ] **Rate Limiting**
  - [ ] `/ai/predict`: 60 RPM per user+IP (token-bucket)
  - [ ] slowapi or Redis-based limiter
- [ ] **Secrets Management**
  - [ ] Document KMS/1Password/Doppler integration plan
  - [ ] `.env.docker` permissions audit (chmod 600)

#### DoD (Definition of Done):

✅ All CI pipelines green  
✅ Protected branch rules enabled (`main` requires CI pass)  
✅ JWT login working (test: `POST /auth/login`)  
✅ Rate limit returns 429 on breach  
✅ Secrets audit doc created

---

### 📅 Gün 2 — Veri Hijyeni & Reproducibility 📐

**Mantık:** Model güvenliği için foundation

#### Tasks:

- [ ] **Feature Store Schema v1**
  - [ ] DuckDB schema freeze: `features.yml` + data dictionary
  - [ ] Parquet export for training snapshots
  - [ ] Schema validation in `feature_store.py`
- [ ] **Training Data Freeze**
  - [ ] Every training run: `data_snapshot_id` (timestamp + checksum)
  - [ ] Save snapshot metadata: `backend/data/models/{run_id}/data_snapshot.json`
- [ ] **Model Card v2 Template**
  - [ ] Train window (start/end dates)
  - [ ] Split strategy (by-time, no leakage)
  - [ ] Metrics: AUC, PR-AUC, Kappa, Hitrate, Calibration
  - [ ] Feature importance top-20
  - [ ] Leakage checks: future info guard test results
- [ ] **Leakage Guard Tests**
  - [ ] CI test: no features with `shift(-N)` where N < 0
  - [ ] Time-based split enforced (train < val < test)
- [ ] **Feature Versioning**
  - [ ] `features_v1.parquet` + git tag
  - [ ] Symlink `features_latest.parquet`

#### DoD:

✅ `features.yml` committed + CI validates schema  
✅ Data snapshot JSON auto-generated on training  
✅ Model card v2 template filled for 1 sample model  
✅ Leakage guard tests pass in CI  
✅ Feature version symlink script working

---

### 📅 Gün 3 — LGBM Production Training (Real) 🤖

**Mantık:** Gerçek model, kalibrasyon, latency ölçümü

#### Tasks:

- [ ] **Optuna Hyperparameter Tuning**
  - [ ] 200+ trials, early stopping (patience=50)
  - [ ] Metrics: logloss + custom (profit-weighted)
  - [ ] Class imbalance: `scale_pos_weight` if needed
- [ ] **Probability Calibration**
  - [ ] Platt scaling or isotonic regression
  - [ ] Calibration plot (reliability diagram) → save PNG
- [ ] **Latency Benchmarking**
  - [ ] Warm-up: 100 inferences (ignore)
  - [ ] Measure 1000 inferences: p50, p90, p95, p99
  - [ ] Save to `model_card.json`
- [ ] **Model Card Generation**
  - [ ] Auto-generate from training run metadata
  - [ ] Include: accuracy, Kappa, AUC, PR-AUC, calibration score
  - [ ] Feature importance chart
- [ ] **Deployment**
  - [ ] Save to `backend/data/models/{run_id}/lgbm.pkl`
  - [ ] Update symlink `best_lgbm.pkl` → new model
  - [ ] Rollback script: `scripts/rollback_model.sh {prev_run_id}`

#### DoD:

✅ LGBM accuracy ≥65% (validation)  
✅ Calibration ECE < 0.1  
✅ Inference p95 ≤ 80ms (CPU, no cache)  
✅ Model card generated with all fields  
✅ Symlink updated + rollback tested

---

### 📅 Gün 4 — TFT Production Training (Real) 🧠

**Mantık:** Proper TFT + drift hooks

#### Tasks:

- [ ] **Sequence Dataset Builder**
  - [ ] Sliding window: seq_len=60, horizon=5
  - [ ] Time-based split (no shuffle)
  - [ ] Normalization: save scaler state
- [ ] **Lightning Trainer**
  - [ ] Early stopping (val_loss, patience=10)
  - [ ] Small but realistic: hidden_size=64, layers=2
  - [ ] Export: `state_dict` + scaler + config JSON
- [ ] **Inference Wrapper**
  - [ ] Replace placeholder in `infer_tft.py`
  - [ ] Latency benchmark: p95 ≤ 40ms (CPU)
- [ ] **Drift Detection Hooks**
  - [ ] PSI (Population Stability Index) on input features
  - [ ] Script: `scripts/check_drift.py` (daily cron)
  - [ ] Alert if PSI > 0.2
- [ ] **Model Card TFT**
  - [ ] Same v2 template
  - [ ] Add: seq_len, horizon, hidden_size

#### DoD:

✅ TFT training completes with early stopping  
✅ Real inference working (not placeholder)  
✅ Inference p95 ≤ 40ms  
✅ Drift script runs + logs PSI  
✅ TFT card generated, ensemble updated

---

### 📅 Gün 5 — Backtest & Raporlama 📊

**Mantık:** Gerçekçi friction, benchmark karşılaştırması, CI guard

#### Tasks:

- [ ] **Vectorized Backtest Runner**
  - [ ] 90-day window (or max available)
  - [ ] Realistic fees: 10 bps maker, 15 bps taker
  - [ ] Slippage: 5 bps (configurable)
  - [ ] Position sizing: fixed % (e.g. 10% equity per trade)
- [ ] **Metrics Suite**
  - [ ] Sharpe, Sortino, Max Drawdown (MDD)
  - [ ] Turnover, Hit Rate, Profit Factor
  - [ ] Vol, Tail Risk (VaR 95%)
  - [ ] **Benchmark**: Buy & Hold for same period
- [ ] **HTML Report Generator**
  - [ ] Equity curve chart (plotly/matplotlib)
  - [ ] Drawdown underwater plot
  - [ ] Monthly returns heatmap
  - [ ] Trade distribution histogram
  - [ ] Comparison table: Strategy vs B&H
- [ ] **JSON Export**
  - [ ] Machine-readable: all metrics + trades
  - [ ] Save to `reports/backtests/{symbol}_{date}.json`
- [ ] **CI Guard (Nightly)**
  - [ ] Run backtest on commit to `main`
  - [ ] Fail if Sharpe drops >10% vs baseline
  - [ ] Alert: auto-rollback candidate

#### DoD:

✅ Backtest runs for BTC/ETH/SOL (90d)  
✅ HTML reports generated + saved  
✅ Strategy Sharpe ≥ B&H + 0.5 (incremental target)  
✅ CI nightly job configured  
✅ Reports visible in frontend (`/backtest` page)

---

### 📅 Gün 6 — Operasyonel Sertifikasyon 🛡️

**Mantık:** Chaos testing, alerts tuning, backups

#### Tasks:

- [ ] **Kill Switch Chaos Test**
  - [ ] Inject: burst 100 errors in 10s
  - [ ] Inject: MD throttle (simulate MEXC 429)
  - [ ] Measure: MTTR (Mean Time To Recovery)
  - [ ] Target: MTTR < 2 min
  - [ ] Document: `docs/KILL_SWITCH_CHAOS_REPORT.md`
- [ ] **Alerts Tuning**
  - [ ] Update `ops/prometheus/alerts.yml`:
    - Inference p95 > 80ms (5m window)
    - Queue depth > 24 (p95)
    - Error rate > 0.5% (5m window)
  - [ ] Add **runbook links** to each alert
  - [ ] Test alert delivery: email/Slack
- [ ] **Backups & Log Rotation**
  - [ ] DuckDB daily backup (retain 7 days)
  - [ ] JSONL rotate + gzip (retain 30 days)
  - [ ] Script: `scripts/backup_daily.sh` (already exists, verify)
  - [ ] Cron setup documented
- [ ] **Ops Runbook Update**
  - [ ] Add: chaos test results
  - [ ] Add: alert response playbooks
  - [ ] Add: rollback procedures

#### DoD:

✅ Chaos test passed (MTTR < 2 min)  
✅ All 15+ alerts configured + tested  
✅ Runbook links added to alerts  
✅ Backup script verified (manual run)  
✅ Ops runbook updated + reviewed

---

### 📅 Gün 7 — 24h Soak + GO/NO-GO 🚀

**Mantık:** Live test, post-mortem, production readiness decision

#### Tasks:

- [ ] **24h Paper Trading Run**
  - [ ] 3-5 symbols (BTC, ETH, SOL, BNB, ADA)
  - [ ] Monitor checkpoints: T+1h, T+6h, T+12h, T+24h
  - [ ] Collect metrics:
    - Inference p95, p99
    - Drop rate (SSE/MD)
    - Error rate (5m buckets)
    - CPU/RAM usage
    - Trade count, PnL
- [ ] **Post-Mortem Light**
  - [ ] List all alerts triggered
  - [ ] Identify anomalies (if any)
  - [ ] Recommended parameter tweaks
  - [ ] Document: `reports/24H_SOAK_REPORT.md`
- [ ] **GO/NO-GO Decision**
  - [ ] Checklist:
    - [ ] Inference p95 < 80ms? ✅/❌
    - [ ] Drop rate ≤ 0.1%? ✅/❌
    - [ ] Error rate < 0.5%? ✅/❌
    - [ ] Zero crashes? ✅/❌
    - [ ] MTTR < 2 min? ✅/❌
  - [ ] If GO: prepare prod keys + IP allowlist
  - [ ] If NO-GO: create follow-up sprint backlog
- [ ] **Production Transition Plan**
  - [ ] Real API keys (MEXC production)
  - [ ] IP allowlist for prod API
  - [ ] Audit log enabled
  - [ ] Monitoring dashboards live
  - [ ] On-call rotation defined

#### DoD:

✅ 24h run completes without crashes  
✅ Post-mortem report published  
✅ GO/NO-GO decision documented  
✅ If GO: prod transition checklist 100%  
✅ If NO-GO: sprint backlog prioritized

---

## 🎯 Revize KPI/SLO'lar (Enterprise-Grade)

| Kategori          | SLO/Target             | Ölçüm Metodu                    | Not                                   |
| ----------------- | ---------------------- | ------------------------------- | ------------------------------------- |
| **Inference p95** | **< 80ms (CPU)**       | Prometheus histogram            | Cache off ölçümü ayrı sakla           |
| **Drop rate**     | **≤ 0.1%**             | SSE/MD disconnect count         | Transient retry'ler ayrı izle         |
| **Error rate**    | **< 0.5% (5m window)** | Failed requests / total         | Circuit breaker threshold: 5%         |
| **Kill MTTR**     | **< 2 min**            | Chaos test measurement          | From trigger to all engines stopped   |
| **Backtest**      | **Sharpe ≥ B&H + 0.5** | 90-day rolling window           | Incremental target (not absolute 2.0) |
| **Drift PSI**     | **< 0.2 (daily)**      | Feature distribution comparison | Alert + investigate if breached       |
| **Uptime**        | **≥ 99%**              | API `/health` availability      | Excludes planned maintenance          |
| **Coverage**      | **≥ 75% (backend)**    | pytest-cov                      | CI gate                               |
|                   | **≥ 50% (frontend)**   | Vitest coverage                 | CI gate                               |

---

## 🧨 Riskler & Önlemler

| Risk                               | Impact | Prob | Mitigation                                                                |
| ---------------------------------- | ------ | ---- | ------------------------------------------------------------------------- |
| **API rate limit / borsa kesinti** | HIGH   | MED  | Exponential backoff, circuit breaker, 30s TTL cache (optional)            |
| **Data leakage**                   | CRIT   | LOW  | Time-based split enforced, CI guard tests, manual feature audit           |
| **Model regression**               | HIGH   | MED  | Nightly backtest CI gate, auto-rollback symlink, A/B test in prod         |
| **Saat senkronu / drift**          | MED    | LOW  | NTP validation, bar alignment unit tests                                  |
| **Güvenlik breach**                | CRIT   | LOW  | JWT/RBAC, IP allowlist, audit log, secrets KMS, penetration test (Q2)     |
| **LGBM/TFT accuracy < 65%**        | HIGH   | MED  | More features, longer training, ensemble weighting, sentiment integration |
| **Latency spike > 100ms**          | MED    | MED  | Caching, async processing, load balancing, profiling (py-spy)             |

---

## 📋 Definition of Done (7 Gün Sonrası)

### ✅ Must Have (GO-Live Blockers)

- ✅ CI/CD pipelines green (backend + frontend)
- ✅ JWT/RBAC v1 working (3 roles)
- ✅ Rate limiting enforced (60 RPM `/ai/predict`)
- ✅ Feature store schema v1 frozen + validated
- ✅ LGBM trained (≥65% accuracy, p95 ≤80ms, calibrated)
- ✅ TFT trained (real inference, p95 ≤40ms)
- ✅ Model cards v2 generated (both models)
- ✅ Backtest reports (3 symbols, 90d, HTML+JSON)
- ✅ Kill switch chaos tested (MTTR < 2 min)
- ✅ Alerts configured (15+) + runbook links
- ✅ 24h soak test passed (all SLO'lar green)
- ✅ GO/NO-GO decision documented

### 🟡 Should Have (Post-Launch)

- 🟡 Sentiment integration (real, not 0.0)
- 🟡 Drift detection automated (daily cron)
- 🟡 Frontend kill switch button
- 🟡 Position management UI
- 🟡 Secrets KMS integration (Doppler/1Password)

### 🔵 Nice to Have (Future)

- 🔵 Multi-model ensemble (XGBoost, CatBoost)
- 🔵 RL agent (PPO/DQN)
- 🔵 Auto-tuning hyperparameters
- 🔵 Multi-exchange support
- 🔵 Distributed tracing (OpenTelemetry)

---

## 🎯 İlk Adımlar (Bugün - Oct 15, Gün 1)

```bash
# 1. Create CI workflow files
mkdir -p .github/workflows
touch .github/workflows/backend-ci.yml
touch .github/workflows/frontend-ci.yml

# 2. Implement JWT middleware
touch backend/src/app/middleware/auth.py
touch backend/src/app/middleware/rate_limit.py

# 3. Create feature store schema
touch backend/src/data/features.yml

# 4. Audit secrets
ls -la backend/*.env* ops/*.env* .env*

# 5. Start Gün-1 implementation
# (CI/CD + JWT/RBAC focus)
```

---

**Version:** 2.0 (Enterprise-Hardened)  
**Philosophy:** Emniyet Kemeri Önce, Hız Sonra  
**Next Review:** October 18, 2025 (after Gün 3)

---

**Next Review:** October 18, 2025

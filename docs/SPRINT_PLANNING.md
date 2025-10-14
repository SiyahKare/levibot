# 🎯 LeviBot Sprint Planlama - Execution Guide

**Dönem:** Q4 2025 - Q1 2026  
**Takım:** 1-2 Developer (Full-stack/Backend ağırlıklı)  
**Sprint Süresi:** 2 hafta  
**Güncelleme:** 13 Ekim 2025

---

## 📋 Sprint Template (Her Sprint İçin)

### Sprint Başlangıç (Day 0)

- [ ] Sprint planning meeting (2 saat)
- [ ] User story estimation (Planning Poker)
- [ ] Sprint backlog finalize
- [ ] Technical spike'lar belirle

### Sprint Ortası (Day 4-5)

- [ ] Mid-sprint check-in (30dk)
- [ ] Blocker review
- [ ] Scope adjustment (gerekirse)

### Sprint Sonu (Day 9-10)

- [ ] Sprint review/demo (1 saat)
- [ ] Sprint retrospective (1 saat)
- [ ] Deploy to production (Friday evening/Saturday morning)
- [ ] Post-deployment monitoring (48 saat)

### Günlük Aktiviteler

- [ ] Daily standup (15dk, async Slack'te de olabilir)
- [ ] Code review (her PR için)
- [ ] Test yazımı (her feature için)
- [ ] Documentation update (değişiklik olduğunda)

---

## 🚀 SPRINT 9: Production Hardening (2 Hafta)

**Tarih:** 14 Ekim - 27 Ekim 2025  
**Hedef:** %99.5 uptime, production-ready stability  
**Story Points:** 40 (velocity: 20 SP/week)

### Week 1: Database & Error Handling

#### Epic 1: Database Optimization (12 SP)

**Story 9.1.1: ClickHouse Query Optimization** (5 SP)

```
AS A platform operator
I WANT ClickHouse queries to run faster
SO THAT dashboard loads in <2 seconds

Acceptance Criteria:
- [ ] Event query index'leri optimize edildi (ts, event_type, symbol)
- [ ] Partition pruning stratejisi dokümante edildi
- [ ] Query performance profiling dashboard'u (Grafana)
- [ ] Top 10 slow query'ler tespit edilip optimize edildi

Technical Tasks:
- [ ] EXPLAIN ANALYZE ile slow query'leri tespit et
- [ ] Composite index'ler ekle (ts, event_type), (symbol, ts)
- [ ] Materialized view oluştur (hourly aggregations)
- [ ] TTL policy test et (30d retention)

Verification:
curl -s "http://localhost:8000/events?limit=100" -o /dev/null -w "%{time_total}\n"
# Expected: <0.5s (şu an: varies)
```

**Story 9.1.2: TimescaleDB Continuous Aggregate Tuning** (4 SP)

```
AS A ML engineer
I WANT feature staleness to be <30 seconds
SO THAT predictions are always fresh

Acceptance Criteria:
- [ ] m1s aggregate refresh latency <10s
- [ ] m5s aggregate refresh latency <30s
- [ ] Connection pooling (pgbouncer or asyncpg pool)
- [ ] Read replica evaluation & plan

Technical Tasks:
- [ ] Tune refresh policy (REFRESH MATERIALIZED VIEW m1s WITH NO DATA)
- [ ] asyncpg pool size optimization (min: 5, max: 20)
- [ ] Slow query log analysis
- [ ] Chunk time interval review (current: 1 day, optimal: ?)

Verification:
SELECT extract(epoch from (now() - MAX(ts))) FROM tick_m1s;
# Expected: <30s
```

**Story 9.1.3: Redis Optimization & High Availability** (3 SP)

```
AS A SRE
I WANT Redis to handle 10K RPS without memory issues
SO THAT rate limiting doesn't become bottleneck

Acceptance Criteria:
- [ ] Memory policy tuning (allkeys-lru vs allkeys-lfu)
- [ ] Key expiration strategy (TTL optimization)
- [ ] Redis Sentinel setup plan (3-node)
- [ ] Memory usage monitoring (Prometheus alerts)

Technical Tasks:
- [ ] redis-cli --bigkeys analizi
- [ ] Eviction policy test (max memory limit)
- [ ] Connection pooling (aioredis)
- [ ] Sentinel config (ops/redis/sentinel.conf)

Verification:
redis-cli INFO memory | grep used_memory_human
redis-cli INFO stats | grep instantaneous_ops_per_sec
# Expected: <1GB memory, 1000+ ops/sec
```

#### Epic 2: Error Handling & Resilience (10 SP)

**Story 9.2.1: Circuit Breaker Standardization** (3 SP)

```
AS A backend developer
I WANT circuit breakers on all external API calls
SO THAT one failing service doesn't cascade

Acceptance Criteria:
- [ ] Circuit breaker decorator (@circuit_breaker)
- [ ] Applied to: CCXT, OpenAI, Reservoir, 0x API calls
- [ ] Prometheus metrics (circuit_state gauge)
- [ ] Auto-recovery after 60s cooldown

Technical Tasks:
- [ ] src/infra/circuit_breaker.py enhancement
- [ ] Decorator application (10+ call sites)
- [ ] Metrics integration
- [ ] Test circuit open/close states

Verification:
# Simulate API failure, check circuit opens
# Wait 60s, check circuit auto-closes
```

**Story 9.2.2: Retry Logic & Exponential Backoff** (3 SP)

```
AS A system integrator
I WANT automatic retries with backoff
SO THAT transient failures auto-recover

Acceptance Criteria:
- [ ] @retry decorator (3 attempts, exponential backoff)
- [ ] Idempotency keys for critical operations
- [ ] Dead letter queue (DLQ) for permanent failures
- [ ] Retry metrics (levibot_retries_total)

Technical Tasks:
- [ ] src/infra/retry.py (tenacity library)
- [ ] Apply to: webhook queue, model inference, DB writes
- [ ] DLQ implementation (Redis list)
- [ ] DLQ consumer (cron job)

Verification:
# Inject network error, observe 3 retries
# Check DLQ after 3 failures
```

**Story 9.2.3: Graceful Degradation Enhancements** (4 SP)

```
AS A product manager
I WANT system to degrade gracefully
SO THAT users always get some response

Acceptance Criteria:
- [ ] Health check hierarchy (critical vs non-critical)
- [ ] Fallback chain (DB → Cache → Stub)
- [ ] User-facing error messages (no stack traces)
- [ ] Service dependency map (diagram)

Technical Tasks:
- [ ] /healthz endpoint tiering (readyz, livez)
- [ ] Fallback logic audit (ensure all paths covered)
- [ ] Error response standardization (JSON schema)
- [ ] Dependency graph (Graphviz diagram)

Verification:
# Stop TimescaleDB, check /healthz still returns 200
# Stop ClickHouse, check dashboard loads with cached data
```

### Week 2: Performance & Observability

#### Epic 3: Performance & Scalability (8 SP)

**Story 9.3.1: API Load Testing & Optimization** (4 SP)

```
AS A performance engineer
I WANT API to handle 100 RPS without degradation
SO THAT we can scale to 1000 users

Acceptance Criteria:
- [ ] Locust/K6 load test suite (100 RPS, 5 min)
- [ ] P95 latency <100ms under load
- [ ] No memory leaks (constant RSS after 1 hour)
- [ ] Horizontal scaling validation (2 API replicas)

Technical Tasks:
- [ ] backend/tests/load/api_load_test.py (Locust)
- [ ] Profiling (py-spy flame graph)
- [ ] Memory leak detection (tracemalloc)
- [ ] Docker Compose multi-replica test

Verification:
locust -f backend/tests/load/api_load_test.py --headless -u 100 -r 10 -t 5m
# Expected: P95 <100ms, 0 errors
```

**Story 9.3.2: Database Connection Pool Tuning** (2 SP)

```
AS A DBA
I WANT connection pools sized correctly
SO THAT we don't exhaust DB connections

Acceptance Criteria:
- [ ] asyncpg pool: min=5, max=20
- [ ] Connection leak detection (prometheus metric)
- [ ] Query timeout enforcement (10s hard limit)
- [ ] Long-running query killer (alert if >5s)

Technical Tasks:
- [ ] asyncpg pool config (src/infra/db.py)
- [ ] Connection leak detection (track acquire/release)
- [ ] Query timeout (SET statement_timeout = '10s')
- [ ] Slow query alert (Grafana)

Verification:
SELECT count(*) FROM pg_stat_activity;
# Expected: <20 connections
```

**Story 9.3.3: Multi-Level Caching Strategy** (2 SP)

```
AS A backend architect
I WANT 3-tier caching (L1: memory, L2: Redis, L3: DB)
SO THAT hot paths are sub-millisecond

Acceptance Criteria:
- [ ] L1: functools.lru_cache (100 items)
- [ ] L2: Redis (TTL 60s)
- [ ] L3: Database query
- [ ] Cache hit rate metric (target: >80%)

Technical Tasks:
- [ ] Identify hot paths (top 5 endpoint'ler)
- [ ] L1 cache decorator (@lru_cache)
- [ ] L2 Redis cache helper (get_or_set)
- [ ] Cache metrics (levibot_cache_hits_total, levibot_cache_misses_total)

Verification:
# Call /ai/predict 100 times, check hit rate
curl -s http://localhost:8000/metrics | grep cache_hits
# Expected: >80 hits
```

#### Epic 4: Monitoring & Observability (10 SP)

**Story 9.4.1: Distributed Tracing Setup** (4 SP)

```
AS A DevOps engineer
I WANT distributed tracing
SO THAT I can debug cross-service latency

Acceptance Criteria:
- [ ] OpenTelemetry SDK integration
- [ ] Jaeger backend running (Docker)
- [ ] Trace propagation (HTTP headers)
- [ ] Sample dashboard (Jaeger UI)

Technical Tasks:
- [ ] pip install opentelemetry-*
- [ ] Instrument FastAPI (auto-instrumentation)
- [ ] Jaeger exporter config
- [ ] docker-compose.yml update (Jaeger service)

Verification:
# Make API call, check trace in Jaeger UI
# http://localhost:16686
```

**Story 9.4.2: Log Aggregation (Loki)** (3 SP)

```
AS A SRE
I WANT centralized log search
SO THAT I can debug issues across services

Acceptance Criteria:
- [ ] Promtail → Loki → Grafana pipeline
- [ ] JSONL logs ingested
- [ ] LogQL queries (example: error rate by endpoint)
- [ ] Log retention (7d hot, 30d warm)

Technical Tasks:
- [ ] Docker Compose: Loki + Promtail
- [ ] Promtail config (scrape JSONL files)
- [ ] Grafana data source (Loki)
- [ ] Sample dashboard (error logs, slow requests)

Verification:
# Query logs in Grafana Explore
{job="api"} |= "ERROR"
```

**Story 9.4.3: Custom Dashboards (Trading & ML)** (3 SP)

```
AS A trader
I WANT real-time trading dashboard
SO THAT I can monitor PnL and signals

Acceptance Criteria:
- [ ] Trading dashboard (PnL, win rate, Sharpe, drawdown)
- [ ] ML dashboard (drift, ECE, latency, feature staleness)
- [ ] System health dashboard (CPU, memory, disk, network)
- [ ] Alert dashboard (active alerts, history)

Technical Tasks:
- [ ] ops/grafana/dashboards/trading.json
- [ ] ops/grafana/dashboards/ml_health.json
- [ ] ops/grafana/dashboards/system.json
- [ ] ops/grafana/dashboards/alerts.json

Verification:
# Open Grafana, verify 4 new dashboards
# http://localhost:3000
```

### Sprint 9 Definition of Done

- [ ] All stories completed & tested
- [ ] Code review by peer (or self-review if solo)
- [ ] Unit tests (coverage >70%)
- [ ] Integration tests (E2E happy path)
- [ ] Documentation updated (README, ARCHITECTURE)
- [ ] Deployed to production (Docker Compose)
- [ ] Monitoring in place (Grafana dashboards)
- [ ] Post-deployment validation (smoke test)
- [ ] Retrospective notes documented

---

## 🚀 SPRINT 10: Advanced AI Layer (3 Hafta)

**Tarih:** 28 Ekim - 17 Kasım 2025  
**Hedef:** Self-learning, high-performance AI  
**Story Points:** 60 (velocity: 20 SP/week)

### Week 1: Feature Store Foundation

#### Epic 1: Feature Store (15 SP)

**Story 10.1.1: DuckDB Offline Feature Store** (5 SP)

```
AS A ML engineer
I WANT centralized feature storage
SO THAT training and inference are consistent

Acceptance Criteria:
- [ ] DuckDB schema (features table: symbol, ts, feat_*, label)
- [ ] Batch ingestion (from TimescaleDB hourly)
- [ ] Point-in-time correct queries
- [ ] Parquet export for training

Technical Tasks:
- [ ] backend/src/ml/feature_store.py
- [ ] Schema design (100+ features)
- [ ] ETL pipeline (TimescaleDB → DuckDB)
- [ ] Query helpers (get_features_at, get_training_set)

Verification:
# Ingest 1M rows, query <1s
```

**Story 10.1.2: Redis Online Feature Store** (5 SP)

```
AS A trader
I WANT <10ms feature lookup
SO THAT predictions are real-time

Acceptance Criteria:
- [ ] Redis hash per symbol (BTCUSDT:features)
- [ ] Feature TTL (60s)
- [ ] Batch get (MGET for multiple symbols)
- [ ] Cache warming on restart

Technical Tasks:
- [ ] src/ml/feature_store.py (online_store.py)
- [ ] Redis key design (symbol:features:latest)
- [ ] Batch update pipeline
- [ ] Warmup script

Verification:
redis-cli HGETALL BTCUSDT:features
# Expected: <10ms
```

**Story 10.1.3: Feature Monitoring** (5 SP)

```
AS A ML ops engineer
I WANT drift detection per feature
SO THAT I know when to retrain

Acceptance Criteria:
- [ ] PSI per feature (daily)
- [ ] Feature importance tracking (SHAP)
- [ ] Staleness alert (if data >5 min old)
- [ ] Correlation matrix (detect multicollinearity)

Technical Tasks:
- [ ] backend/scripts/feature_drift.py
- [ ] SHAP value logging
- [ ] Prometheus metrics (feature_psi, feature_staleness)
- [ ] Grafana dashboard

Verification:
# Run drift detection, check PSI scores
```

### Week 2: Model Ensemble

#### Epic 2: Multi-Model Ensemble (15 SP)

**Story 10.2.1: Model Registry** (3 SP)

```
AS A ML scientist
I WANT versioned model storage
SO THAT I can A/B test models

Acceptance Criteria:
- [ ] Model registry (S3 or local filesystem)
- [ ] Metadata (version, training date, metrics)
- [ ] Load/save helpers
- [ ] Active model pointer

Technical Tasks:
- [ ] backend/src/ml/model_registry.py
- [ ] S3 bucket (s3://levibot-models/)
- [ ] Metadata JSON (model_v1.0.0.json)
- [ ] API endpoint (/ai/models/list, /ai/models/activate)

Verification:
curl http://localhost:8000/ai/models/list
```

**Story 10.2.2: Ensemble Stacking** (5 SP)

```
AS A quant
I WANT ensemble of LightGBM + XGBoost + LSTM
SO THAT predictions are robust

Acceptance Criteria:
- [ ] Train 3 base models
- [ ] Meta-learner (logistic regression or linear)
- [ ] Weighted voting (Sharpe-optimized)
- [ ] Backtested performance (Sharpe >1.7)

Technical Tasks:
- [ ] Train XGBoost (backend/scripts/train_xgboost.py)
- [ ] Train LSTM (backend/scripts/train_lstm.py)
- [ ] Ensemble stacker (src/ml/ensemble.py)
- [ ] Backtest (2023-2024 data)

Verification:
# Ensemble Sharpe > individual models
```

**Story 10.2.3: Dynamic Weight Adjustment** (4 SP)

```
AS A system
I WANT weights to adapt to market regime
SO THAT ensemble performance is optimal

Acceptance Criteria:
- [ ] Regime detection (bull, bear, sideways)
- [ ] Weight rebalancing (daily based on shadow PnL)
- [ ] EWMA smoothing (prevent jitter)
- [ ] Prometheus metrics (ensemble_weight)

Technical Tasks:
- [ ] backend/scripts/regime_detector.py
- [ ] backend/scripts/ensemble_tuner.py (enhance)
- [ ] Weight persistence (Redis)
- [ ] Backtest validation

Verification:
# Check weights adapt during 2022 bear market
```

**Story 10.2.4: Meta-Learning Layer** (3 SP)

```
AS A ML researcher
I WANT model-of-models
SO THAT I predict which model will work best

Acceptance Criteria:
- [ ] Feature: recent market regime, volatility, volume
- [ ] Target: which model had best Sharpe last 7 days
- [ ] Simple classifier (Random Forest)
- [ ] Use prediction to route signals

Technical Tasks:
- [ ] Train meta-model
- [ ] Integration with ensemble
- [ ] Metrics tracking
- [ ] A/B test vs fixed weights

Verification:
# Meta-learning routing improves Sharpe by 5-10%
```

### Week 3: RL & AutoML

#### Epic 3: Reinforcement Learning (15 SP)

**Story 10.3.1: Trading Gym Environment** (5 SP)

```
AS A RL engineer
I WANT OpenAI Gym-compatible env
SO THAT I can train RL agents

Acceptance Criteria:
- [ ] State space (features: 50-100 dims)
- [ ] Action space (discrete: long/short/hold or continuous: position size)
- [ ] Reward function (Sharpe ratio, PnL, drawdown penalty)
- [ ] Vectorized env (parallel episodes)

Technical Tasks:
- [ ] backend/src/rl/trading_env.py
- [ ] gym.Env subclass
- [ ] Historical data replay
- [ ] Transaction cost & slippage

Verification:
env = TradingEnv('BTCUSDT', '2023-01-01', '2023-12-31')
obs = env.reset()
obs, reward, done, info = env.step(action)
```

**Story 10.3.2: PPO Agent Training** (5 SP)

```
AS A trader
I WANT trained RL policy
SO THAT I can use it for live trading

Acceptance Criteria:
- [ ] PPO agent (stable-baselines3)
- [ ] Trained on 2 years data
- [ ] Backtested Sharpe >1.5
- [ ] Saved policy (policy.zip)

Technical Tasks:
- [ ] backend/scripts/train_rl_ppo.py
- [ ] Hyperparameter tuning (learning rate, gamma, etc.)
- [ ] Tensorboard logging
- [ ] Model export (ONNX for fast inference)

Verification:
# Run backtest, check Sharpe
```

**Story 10.3.3: RL Policy Serving** (5 SP)

```
AS A backend developer
I WANT RL policy in production
SO THAT it generates live signals

Acceptance Criteria:
- [ ] ONNX runtime integration
- [ ] <10ms inference latency
- [ ] API endpoint (/ai/predict/rl)
- [ ] Shadow mode first (log but don't trade)

Technical Tasks:
- [ ] onnxruntime integration
- [ ] src/ai/rl_policy.py
- [ ] FastAPI endpoint
- [ ] Shadow logging

Verification:
curl -X POST http://localhost:8000/ai/predict/rl \
  -d '{"symbol":"BTCUSDT"}' -H "Content-Type: application/json"
```

#### Epic 4: AutoML (15 SP)

**Story 10.4.1: Automated Feature Selection** (5 SP)

```
AS A data scientist
I WANT automatic feature selection
SO THAT I don't manually pick features

Acceptance Criteria:
- [ ] Boruta algorithm
- [ ] Recursive feature elimination (RFE)
- [ ] SHAP-based importance
- [ ] Select top 50 features (from 200+)

Technical Tasks:
- [ ] backend/scripts/feature_selection.py
- [ ] Integration with training pipeline
- [ ] Feature importance tracking
- [ ] Backtest with selected features

Verification:
# Selected features improve Sharpe by 10%
```

**Story 10.4.2: Hyperparameter Optimization** (5 SP)

```
AS A ML engineer
I WANT automatic hyperparameter tuning
SO THAT models are always optimal

Acceptance Criteria:
- [ ] Optuna integration
- [ ] Bayesian optimization (100 trials)
- [ ] Multi-objective (Sharpe + Drawdown)
- [ ] Best params saved

Technical Tasks:
- [ ] backend/scripts/hyperopt.py
- [ ] Objective function (cross-val Sharpe)
- [ ] Pruning (early stopping for bad trials)
- [ ] Visualization (Optuna dashboard)

Verification:
# Tuned model Sharpe > baseline by 15%
```

**Story 10.4.3: Auto-Scheduler** (5 SP)

```
AS A ML ops engineer
I WANT automatic retraining
SO THAT model is always fresh

Acceptance Criteria:
- [ ] Cron job (daily at 3 AM)
- [ ] Drift-triggered retraining
- [ ] Auto-promotion if new model better
- [ ] Slack notification

Technical Tasks:
- [ ] backend/scripts/auto_retrain.py
- [ ] Drift check integration
- [ ] Model comparison (backtest)
- [ ] Slack webhook

Verification:
# Simulate drift, check auto-retrain
```

### Sprint 10 Definition of Done

- [ ] Feature store serving <10ms
- [ ] Ensemble Sharpe >1.7 (backtest)
- [ ] RL policy trained (shadow mode)
- [ ] AutoML pipeline functional
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Deployed to prod (canary mode)
- [ ] Monitoring dashboards updated

---

## 🎯 Sprint Capacity Planning

### Velocity Estimation (Solo Developer)

- **Week 1:** 15-20 SP (ramp-up, unknowns)
- **Week 2:** 20-25 SP (in flow)
- **Week 3+:** 20-22 SP (sustainable)

### Buffer (20%)

- 80% feature work
- 20% bugs, tech debt, unplanned work

### Örnek Sprint Allocation (20 SP)

- **High Priority Stories:** 12 SP (60%)
- **Medium Priority:** 6 SP (30%)
- **Low Priority / Nice-to-have:** 2 SP (10%)

---

## 📊 Sprint Tracking (Notion/Jira Template)

### Kanban Board

```
| Backlog | Todo | In Progress | Review | Done |
|---------|------|-------------|--------|------|
|   30    |  8   |      2      |   3    |  45  |
```

### Sprint Burndown Chart

```
Story Points
40 |●
35 |  ●
30 |    ●
25 |      ●
20 |        ●●
15 |          ●
10 |            ●
 5 |              ●
 0 |________________●
   D1 D2 D3 D4 D5 D6 D7 D8 D9 D10
```

### Daily Standup Template (Async Slack)

```
**Yesterday:**
- ✅ Completed Story 9.1.1 (ClickHouse optimization)
- 🚧 Started Story 9.1.2 (TimescaleDB tuning)

**Today:**
- 🎯 Finish Story 9.1.2
- 🎯 Start Story 9.2.1 (Circuit breakers)

**Blockers:**
- ❌ None
```

---

## ✅ Quality Gates (Every Sprint)

### Pre-Merge Checklist

- [ ] Code review (self or peer)
- [ ] Tests passing (pytest)
- [ ] Linter clean (ruff, mypy)
- [ ] Documentation updated
- [ ] Changelog entry (RELEASE_NOTES)

### Pre-Deploy Checklist

- [ ] Smoke test (manual)
- [ ] Load test (automated, if performance-critical)
- [ ] Database migration dry-run
- [ ] Rollback plan documented
- [ ] Monitoring alerts configured

### Post-Deploy Checklist

- [ ] Health check passing
- [ ] No error spike (last 1 hour)
- [ ] Key metrics stable (latency, throughput)
- [ ] User-facing features validated
- [ ] Announce in Slack/Discord

---

## 🔥 Hotfix Process

### Criteria

- Production down (P0)
- Data loss risk (P0)
- Security vulnerability (P0)
- Critical bug (P1)

### Steps

1. **Identify** (5 min) - reproduce, assess impact
2. **Fix** (30 min) - minimal code change
3. **Test** (10 min) - smoke test locally
4. **Deploy** (5 min) - skip CI, manual deploy
5. **Monitor** (1 hour) - watch metrics, logs
6. **Post-mortem** (next day) - root cause, prevention

### Communication

- Slack: #incidents channel
- Status page update (if user-facing)
- Post-mortem doc (template: docs/POST_MORTEM_TEMPLATE.md)

---

## 🎉 Sprint Retrospective Template

### What Went Well? ✅

- Feature X shipped on time
- Test coverage increased to 75%
- Zero production incidents

### What Went Wrong? ❌

- Story Y took 2x estimated time
- Blocked on external API issue
- Missed code review SLA (24h)

### Action Items 🎯

- [ ] Improve estimation (use historical data)
- [ ] Add circuit breaker for external API
- [ ] Set up auto-reminder for pending PRs

---

## 📈 Metrics to Track (Weekly)

### Velocity

```
Sprint 1: 18 SP
Sprint 2: 22 SP
Sprint 3: 20 SP (stable)
```

### Quality

```
Bug count: 3 → 2 → 1 (decreasing)
Test coverage: 65% → 70% → 75% (increasing)
```

### Performance

```
P95 latency: 50ms → 30ms → 20ms (improving)
Uptime: 99.0% → 99.5% → 99.7% (improving)
```

---

## 🧰 Developer Toolkit

### Must-Have Tools

- **IDE:** VS Code (with Python, ESLint, Prettier extensions)
- **API Testing:** Postman/Insomnia, curl
- **DB Client:** DBeaver (PostgreSQL, ClickHouse)
- **Monitoring:** Grafana, Jaeger, Redis CLI
- **Profiling:** py-spy, cProfile

### Productivity Hacks

- **Code snippets:** VS Code snippets (FastAPI route, pytest fixture)
- **Shell aliases:** `alias ll='ls -lah'`, `alias gs='git status'`
- **Makefile shortcuts:** `make test`, `make run`, `make deploy`
- **Docker shortcuts:** `docker compose up -d`, `docker compose logs -f api`

---

**Son Güncelleme:** 13 Ekim 2025  
**Sahip:** Onur Mutlu (@siyahkare)  
**Format:** Living document (güncellenecek)

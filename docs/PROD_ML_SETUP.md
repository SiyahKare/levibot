# Production ML Setup Guide

Complete guide for deploying real-time ML predictions in production.

---

## 🎯 Quick Start (10 minutes)

### Prerequisites

- Docker & Docker Compose running
- PostgreSQL/TimescaleDB accessible
- MEXC WebSocket feed configured (optional, can use test data)

### Step-by-Step

```bash
# 1. Start services
docker compose up -d timescaledb redis

# 2. Setup continuous aggregates (m1s, m5s candles)
make ca-setup

# 3. Seed test data (if MEXC WS not available yet)
make seed-data

# 4. Train production model
make train-prod

# 5. Restart backend with new model
make backend-restart

# 6. Test predictions
make model-test

# 7. Open panel
open http://localhost:3002
```

---

## 📊 Data Pipeline

### 1. Market Data Ingestion

**MEXC WebSocket → market_ticks table**

Check if data is flowing:

```bash
docker compose exec timescaledb psql -U postgres -d levibot \
  -c "SELECT symbol, COUNT(*) FROM market_ticks
      WHERE ts > NOW() - INTERVAL '60 seconds'
      GROUP BY symbol;"
```

**Expected:** ≥100 ticks/minute per symbol

**If no data:**

- Check MEXC WS connection: `docker compose logs api | grep mexc`
- Seed test data: `make seed-data`

### 2. Continuous Aggregates

**m1s (1-second candles)** and **m5s (5-second candles)** provide pre-aggregated OHLC data for fast feature computation.

Setup:

```bash
make ca-setup
```

Verify:

```bash
docker compose exec timescaledb psql -U postgres -d levibot \
  -c "SELECT symbol, MAX(t) AS latest, COUNT(*)
      FROM m1s
      WHERE t > NOW() - INTERVAL '1 hour'
      GROUP BY symbol;"
```

**Expected:** Recent timestamps (<60s ago), >3000 rows/hour

### 3. Feature Engineering

**Features V2** (`backend/src/ai/features_v2.py`) computes:

- `ret_1m, ret_5m`: Returns over 1m and 5m
- `vol_1m, vol_5m`: Volatility (rolling std/mean)
- `rsi_14`: RSI indicator (14-period)
- `zscore_60`: Z-score vs 60s window

**Staleness check:** If last data >60s → fallback to stub-sine

Test features:

```bash
curl 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s&model=skops-local' | jq
```

Check response:

- `staleness_s` < 60 → ✅ Fresh data
- `fallback: true` → ⚠️ Stale data or DB error

---

## 🤖 Model Training & Deployment

### Training Pipeline

**Script:** `backend/scripts/train_prod_model.py`

```bash
# Train with default settings (28 days, LogisticRegression)
make train-prod

# Or customize:
TRAIN_DAYS=14 MODEL_TYPE=gb .venv/bin/python backend/scripts/train_prod_model.py
```

**Output:**

- `ops/models/model.skops` - Trained model (joblib)
- `ops/models/meta.json` - Metadata (version, features, metrics)

**Metadata example:**

```json
{
  "version": "v1.0.0",
  "trained_at": "2025-10-10T20:30:00",
  "symbol": "BTCUSDT",
  "features": ["ret_1m", "ret_5m", "vol_1m", "vol_5m", "rsi_14", "zscore_60"],
  "horizon": "60s",
  "model_type": "LogisticRegression",
  "metrics": {
    "train_acc": 0.994,
    "test_acc": 0.99
  }
}
```

### Model Selection

**Available models:**

- `stub-sine` - Sine-wave test model (always available)
- `skops-local` - Production model (from `ops/models/model.skops`)

**Switch model:**

```bash
# Via API
curl -s -X POST http://localhost:8000/ai/select \
  -H 'Content-Type: application/json' \
  -d '{"name":"skops-local"}' \
  -b cookies.txt | jq

# Via panel
# → Overview → Model Selector → Select "skops-local"
```

**Persistence:** Model selection is persisted to `flags.yaml` and survives restarts.

---

## 📈 Monitoring & Metrics

### Prometheus Metrics

All metrics are exposed at `http://localhost:8000/metrics`

**Key metrics:**

| Metric                               | Type    | Description                                  |
| ------------------------------------ | ------- | -------------------------------------------- |
| `levibot_model_latency_seconds`      | Summary | Prediction latency (p50, p95, p99)           |
| `levibot_predict_requests_total`     | Counter | Total predictions (by model, symbol, status) |
| `levibot_model_errors_total`         | Counter | Prediction errors (by model, error_type)     |
| `levibot_fallback_events_total`      | Counter | Fallback events (by reason)                  |
| `levibot_features_staleness_seconds` | Gauge   | Data staleness per symbol                    |
| `levibot_market_ticks_per_minute`    | Gauge   | Tick rate per symbol                         |
| `levibot_active_model_info`          | Gauge   | Currently active model (1=active)            |
| `levibot_model_switches_total`       | Counter | Model switch events                          |

### Alerts (Prometheus Rules)

Create `ops/prometheus/rules.yml`:

```yaml
groups:
  - name: levibot_ml
    interval: 30s
    rules:
      # Data staleness alert
      - alert: DataStale60s
        expr: levibot_features_staleness_seconds > 60
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Market data stale for {{ $labels.symbol }}"
          description: "No fresh data for {{ $value }}s"

      # High latency alert
      - alert: ModelLatencyP95High
        expr: histogram_quantile(0.95, levibot_model_latency_seconds) > 0.3
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High prediction latency (p95 > 300ms)"

      # Error rate spike
      - alert: PredictErrorSpike
        expr: rate(levibot_model_errors_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Prediction error rate > 1%"

      # Tick rate drop
      - alert: TicksDrop
        expr: levibot_market_ticks_per_minute < 30
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Market tick rate dropped for {{ $labels.symbol }}"
```

### Panel Health Indicators

**Overview Page:**

- **Model Selector** - Shows current model + switch buttons
- **Recent Predictions** - Live prediction feed with prob_up scores
- **Data staleness badge** - 🟢 Fresh / 🟡 Stale / 🔴 Error

**Ops Page:**

- **Metrics Health** - Real-time status of prediction latency, error rate, data freshness

---

## 🚀 Production Checklist

### Pre-Deploy

- [ ] TimescaleDB running and healthy
- [ ] market_ticks receiving ≥100 ticks/min
- [ ] Continuous aggregates (m1s, m5s) refreshing
- [ ] Model trained and saved to `ops/models/model.skops`
- [ ] Metrics exposed at `/metrics`
- [ ] Prometheus alerts configured

### Go-Live

```bash
# 1. Final model training
make train-prod

# 2. Backend restart
make backend-restart

# 3. Select production model
curl -X POST http://localhost:8000/ai/select \
  -H 'Content-Type: application/json' \
  -d '{"name":"skops-local"}' \
  -b cookies.txt

# 4. Smoke test
make model-test

# 5. Monitor for 15 minutes
watch -n 5 'curl -s http://localhost:8000/metrics | grep levibot_model_latency'
```

### Post-Deploy Validation

- [ ] Prediction latency p95 < 200ms
- [ ] Error rate < 0.1%
- [ ] Fallback rate < 5%
- [ ] Data staleness < 60s
- [ ] Panel showing live predictions

---

## 🔧 Troubleshooting

### Issue: "DB pool not initialized"

**Cause:** Database connection failed

**Fix:**

```bash
# Check DB credentials in .env
cat .env | grep DB_

# Test connection
docker compose exec timescaledb psql -U postgres -d levibot -c "SELECT 1;"

# Restart backend
make backend-restart
```

### Issue: "No market data available" / High staleness

**Cause:** market_ticks table empty or MEXC WS down

**Fix:**

```bash
# Check tick count
docker compose exec timescaledb psql -U postgres -d levibot \
  -c "SELECT COUNT(*) FROM market_ticks WHERE ts > NOW() - INTERVAL '5 minutes';"

# If zero, seed test data
make seed-data

# Or check MEXC WS
docker compose logs api | grep mexc | tail -20
```

### Issue: Silent fallback to stub-sine

**Expected behavior!** This is production-safe. Check reason:

```bash
curl 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s&model=skops-local' | jq '.fallback_reason'
```

**Common reasons:**

- `DB pool init failed` → DB connection issue
- `Data stale: 120s` → MEXC WS down or m1s not refreshing
- `Model error` → model.skops corrupted or incompatible

---

## 📚 Additional Resources

- [Features V2 Source](../backend/src/ai/features_v2.py)
- [Model Provider](../backend/src/ai/model_provider.py)
- [Training Script](../backend/scripts/train_prod_model.py)
- [Metrics](../backend/src/infra/metrics.py)
- [Makefile Targets](../Makefile)

---

## 🎯 Performance Targets

| Metric                   | Target   | Current  |
| ------------------------ | -------- | -------- |
| Prediction latency (p95) | <200ms   | ~35ms ✅ |
| Error rate               | <0.1%    | TBD      |
| Fallback rate            | <5%      | TBD      |
| Data staleness           | <60s     | TBD      |
| Tick rate                | >100/min | TBD      |

---

**Questions?** Check `make help` or ping @devran 💙

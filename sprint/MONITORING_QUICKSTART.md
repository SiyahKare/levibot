# 📊 Monitoring & Soak Test — Quick Start

**Date:** 13 Ekim 2025  
**Status:** ✅ COMPLETE

---

## 📦 Tamamlanan Bileşenler

### 1. Prometheus Metrics

- ✅ `backend/src/metrics/metrics.py` (120 lines)
  - Engine lifecycle metrics (uptime, heartbeat, status, errors)
  - Inference/signal metrics (latency, prob, confidence, signals)
  - Risk/portfolio metrics (equity, PnL, positions, global stop)
  - Export functions for easy integration

### 2. Engine Integration

- ✅ Modified `backend/src/engine/engine.py`
  - Health metrics export (every cycle)
  - Inference latency tracking
  - Signal metrics export

### 3. Risk Integration

- ✅ Modified `backend/src/app/routers/risk.py`
  - Risk metrics export on `/risk/summary`

### 4. API Endpoint

- ✅ `backend/src/app/routers/metrics.py`
  - `GET /metrics/prom` - Prometheus scrape endpoint

### 5. Prometheus Config

- ✅ `ops/prometheus.yml`
  - 5s scrape interval
  - LeviBot job configuration

### 6. Soak Test Script

- ✅ `scripts/soak_test.py`
  - Configurable duration/symbols
  - Real-time monitoring
  - Summary statistics
  - Pass/fail determination

### 7. Grafana Dashboard

- ✅ `ops/grafana-dashboard.json`
  - 8 panels (equity, PnL, stop, latency, signals, status, positions, errors)
  - 5s auto-refresh
  - Import-ready JSON

---

## 🚀 Quick Start

### 1. Start LeviBot API

```bash
cd backend
source venv/bin/activate
uvicorn src.app.main:app --reload
```

### 2. Check Metrics Endpoint

```bash
curl http://localhost:8000/metrics/prom
```

Expected output:

```
# HELP levi_engine_uptime_seconds Engine uptime in seconds
# TYPE levi_engine_uptime_seconds gauge
levi_engine_uptime_seconds{symbol="BTCUSDT"} 45.23
...
```

### 3. Start Prometheus (Local)

**Option A: Binary**

```bash
# Download Prometheus from https://prometheus.io/download/
prometheus --config.file=ops/prometheus.yml
```

**Option B: Docker**

```bash
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/ops/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

Open: http://localhost:9090

### 4. Setup Grafana (Optional but Recommended)

**Start Grafana:**

```bash
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

**Configure:**

1. Open http://localhost:3000 (login: admin/admin)
2. Add Data Source → Prometheus → URL: `http://host.docker.internal:9090`
3. Import Dashboard → Upload `ops/grafana-dashboard.json`

### 5. Run Soak Test

**30-minute test (default):**

```bash
cd /Users/onur/levibot
python scripts/soak_test.py
```

**Custom configuration:**

```bash
# 60-minute test with 6 symbols
API=http://localhost:8000 \
SYMBOLS="BTCUSDT,ETHUSDT,SOLUSDT,ARBUSDT,LINKUSDT,DOGEUSDT" \
DURATION_MIN=60 \
python scripts/soak_test.py
```

**Expected output:**

```
============================================================
🧪 LeviBot Soak Test
============================================================
API: http://localhost:8000
Symbols: BTCUSDT, ETHUSDT, SOLUSDT, ATOMUSDT, AVAXUSDT
Duration: 30 minutes
Poll interval: 5.0s
============================================================

🚀 Starting engines...
  ✅ BTCUSDT: started
  ✅ ETHUSDT: started
  ...

⏱️  Starting 30 minute soak test...

[   0s] running=5/5 uptime=0.0s errs=0 equity=$10000.00 pnl=+0.00% pos=0
[   5s] running=5/5 uptime=5.0s errs=0 equity=$10000.00 pnl=+0.00% pos=0
...
```

---

## 📊 Available Metrics

### Engine Lifecycle

- `levi_engine_uptime_seconds{symbol}` - Engine uptime
- `levi_engine_last_heartbeat{symbol}` - Last heartbeat timestamp
- `levi_engine_status{symbol}` - Status (0=stopped, 1=running, 2=crashed)
- `levi_engine_errors_total{symbol}` - Total errors

### Inference / Signals

- `levi_inference_latency_seconds{symbol}` - ML inference latency (histogram)
- `levi_signal_prob_up{symbol}` - Probability of price increase
- `levi_signal_confidence{symbol}` - Model confidence
- `levi_signals_total{symbol,side}` - Total signals (long/short/flat)

### Risk / Portfolio

- `levi_equity_now` - Current equity
- `levi_realized_today_pct` - Daily realized PnL %
- `levi_positions_open` - Number of open positions
- `levi_global_stop` - Global stop active (1=yes, 0=no)

---

## 🎯 Soak Test Success Criteria

✅ **Pass Criteria:**

- Zero crashes during test period
- All engines running at end of test
- Inference latency p95 < 100ms
- Error count stable (no continuous growth)
- Memory usage stable (no leaks)

❌ **Fail Criteria:**

- Any engine crashes
- Engines stopped unexpectedly
- Error rate continuously increasing
- Memory usage continuously increasing

---

## 📈 Example Queries

### Prometheus Queries

**Average inference latency (last 5m):**

```promql
histogram_quantile(0.95, sum(rate(levi_inference_latency_seconds_bucket[5m])) by (le, symbol))
```

**Total signals by side:**

```promql
sum(increase(levi_signals_total[1h])) by (side)
```

**Engines currently running:**

```promql
count(levi_engine_status == 1)
```

**Daily PnL trend:**

```promql
levi_realized_today_pct
```

---

## 🔧 Troubleshooting

### Metrics endpoint returns 404

- Check if metrics router is registered in `main.py`
- Verify prometheus_client is installed: `pip install prometheus-client`

### Prometheus can't scrape metrics

- Check if API is accessible from Prometheus
- Use `host.docker.internal:8000` if Prometheus is in Docker
- Check Prometheus targets: http://localhost:9090/targets

### Grafana shows "No data"

- Verify Prometheus data source is configured correctly
- Check if metrics are being scraped (Prometheus UI)
- Wait 5-10 seconds for first scrape

### Soak test script fails

- Install aiohttp: `pip install aiohttp`
- Check API is running: `curl localhost:8000/engines/status`
- Verify symbols are valid

---

## 🔜 Next Steps

### Alerting (Recommended)

Create alert rules for:

- Global stop triggered
- Engine crashed
- High error rate
- Inference latency spike

**Example alert rule** (`ops/prometheus-alerts.yml`):

```yaml
groups:
  - name: levibot
    rules:
      - alert: GlobalStopActive
        expr: levi_global_stop == 1
        for: 1m
        annotations:
          summary: "Global stop loss triggered"

      - alert: EngineCrashed
        expr: levi_engine_status == 2
        for: 30s
        annotations:
          summary: "Engine {{$labels.symbol}} crashed"
```

### Production Monitoring

- Set up Alertmanager for Telegram/Slack notifications
- Configure longer retention for Prometheus
- Add application logs to Loki
- Set up distributed tracing with Jaeger

---

**Team:** @siyahkare  
**Date:** 13 Ekim 2025  
**Status:** ✅ MONITORING READY

---

**🎉 Prometheus + Grafana + Soak Test tamamlandı!**

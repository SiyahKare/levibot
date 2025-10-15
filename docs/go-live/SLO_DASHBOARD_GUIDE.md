# SLO Dashboard Monitoring Guide

Real-time monitoring guide for 24h soak test.

---

## Quick Links

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| **SLO Overview** | http://localhost:3000/d/slo-overview | Main SLO tracking |
| **Engine Health** | http://localhost:3000/d/engines | Engine status & heartbeats |
| **ML Performance** | http://localhost:3000/d/ml-perf | Inference latency & accuracy |
| **Market Data** | http://localhost:3000/d/market-data | WS health, drop rate, throughput |
| **Risk Guards** | http://localhost:3000/d/risk | Exposure, drawdown, kill switch |
| **Chaos Metrics** | http://localhost:3000/d/chaos | MTTR, recovery, alerts |

**Grafana Login**: admin / [check `.env.docker`]

---

## 1. SLO Overview Dashboard

### Key Panels

#### API Uptime (Target: ≥ 99.9%)
```promql
avg_over_time(up{job="levibot-api"}[5m]) * 100
```
**Alert**: < 99.9% for 10m → P1

#### Inference p95 Latency
```promql
# LGBM (Target: ≤ 80ms)
histogram_quantile(0.95, rate(levi_inference_latency_ms_bucket{model="lgbm"}[5m]))

# TFT (Target: ≤ 40ms)
histogram_quantile(0.95, rate(levi_inference_latency_ms_bucket{model="tft"}[5m]))
```
**Alert**: > target + 20% for 10m → P2

#### Error Rate (Target: ≤ 0.1%)
```promql
rate(levi_errors_total[1m]) / rate(http_requests_total[1m]) * 100
```
**Alert**: > 0.1% for 5m → P1

---

## 2. Engine Health Dashboard

### Key Panels

#### Engine Status Heatmap
```promql
levi_engine_status{symbol=~".*"}
```
**Values**: 1 = running, 0 = stopped

#### Heartbeat Gaps
```promql
time() - levi_engine_last_heartbeat_ts
```
**Alert**: > 60s → P1 (engine down)

#### Engine Uptime (Target: ≥ 99.5%)
```promql
avg_over_time(levi_engine_status[5m]) * 100
```

---

## 3. ML Performance Dashboard

### Key Panels

#### Prediction Latency (p50/p95/p99)
```promql
histogram_quantile(0.50, rate(levi_prediction_duration_seconds_bucket[5m]))
histogram_quantile(0.95, rate(levi_prediction_duration_seconds_bucket[5m]))
histogram_quantile(0.99, rate(levi_prediction_duration_seconds_bucket[5m]))
```

#### Prediction Accuracy (Rolling 1h)
```promql
sum(rate(levi_predictions_correct_total[1h])) / sum(rate(levi_predictions_total[1h])) * 100
```

#### Model Drift (PSI)
```promql
levi_drift_psi_max
```
**Alert**: > 0.25 → P2 (retrain recommended)

---

## 4. Market Data Dashboard

### Key Panels

#### WS Connection Status
```promql
levi_ws_connected{exchange="mexc"}
```
**Values**: 1 = connected, 0 = disconnected

#### MD Drop Rate (Target: ≤ 0.1%)
```promql
rate(levi_md_dropped_total[5m]) / rate(levi_md_received_total[5m]) * 100
```

#### WS Reconnect Count
```promql
increase(levi_ws_reconnects_total[1h])
```
**Alert**: > 5 in 1h → P2

#### Data Staleness
```promql
time() - levi_last_md_ts
```
**Alert**: > 5s → P1

---

## 5. Risk Guards Dashboard

### Key Panels

#### Global Stop Status
```promql
levi_kill_switch
```
**Values**: 1 = active, 0 = inactive

#### Portfolio Drawdown (Target: ≤ 5%)
```promql
levi_portfolio_drawdown_pct
```
**Alert**: > 5% → P0 (kill switch auto-trigger)

#### Position Concentration
```promql
max(levi_position_pct_portfolio)
```
**Alert**: > 30% → P2

#### Equity Curve
```promql
levi_portfolio_equity
```

---

## 6. Chaos Metrics Dashboard

### Key Panels

#### MTTR (Target: ≤ 2min)
```promql
levi_recovery_duration_seconds / 60
```

#### Chaos Test Pass Rate (Target: ≥ 90%)
```promql
levi_chaos_test_pass_rate * 100
```

#### Engine Restart Failures
```promql
increase(levi_engine_restart_failures_total[1h])
```
**Alert**: > 0 → P1

---

## Monitoring Checklist

### Every 15 Minutes
- [ ] Check SLO Overview dashboard
- [ ] Verify all engines running
- [ ] Check for new alerts

### Every Hour
- [ ] Review error logs
- [ ] Check inference latency trends
- [ ] Verify WS connection stable
- [ ] Review paper trading PnL

### Every 4 Hours
- [ ] Deep dive into any P2/P3 alerts
- [ ] Review audit logs
- [ ] Check disk/memory usage
- [ ] Verify backups running

### End of Test (24h)
- [ ] Export all dashboard screenshots
- [ ] Download soak_summary.json
- [ ] Review all alerts (resolved + active)
- [ ] Fill GO/NO-GO template

---

## Alert Response Matrix

| Alert | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| API Down | P0 | Immediate | Restart API, check logs |
| Kill Switch Active | P0 | Immediate | Investigate trigger, manual review |
| Engine Down | P1 | < 5 min | Auto-recover or manual restart |
| High Latency | P2 | < 15 min | Check load, scale if needed |
| WS Disconnect | P2 | < 5 min | Auto-reconnect, verify |
| Chaos Test Fail | P3 | < 1 hour | Review logs, update tests |

---

## Troubleshooting

### API Uptime < 99.9%
1. Check Docker container status: `docker ps`
2. Review API logs: `docker logs levibot-api`
3. Check system resources: `docker stats`
4. Restart if needed: `docker compose restart api`

### Inference Latency Spike
1. Check model load: `curl http://localhost:8000/ai/models`
2. Review Prometheus metrics
3. Restart model service if needed
4. Check for memory leaks

### Engine Not Running
1. Run auto-recover: `./scripts/auto_recover.sh`
2. Check engine logs: `backend/data/logs/engine-*.jsonl`
3. Manual restart: `curl -X POST http://localhost:8000/engines/{id}/start`

### WS Frequent Disconnects
1. Check network stability
2. Review MEXC API status
3. Check rate limiting
4. Restart market data service

---

## Export & Reporting

### Screenshot Checklist
- [ ] SLO Overview (full 24h)
- [ ] Engine Health heatmap
- [ ] Inference latency trends
- [ ] WS connection timeline
- [ ] Equity curve
- [ ] Alert timeline

### Data Export
```bash
# Export Prometheus data
curl -G 'http://localhost:9090/api/v1/query_range' \
  --data-urlencode 'query=up{job="levibot-api"}' \
  --data-urlencode 'start=2025-10-15T09:00:00Z' \
  --data-urlencode 'end=2025-10-16T09:00:00Z' \
  --data-urlencode 'step=300' > api_uptime.json

# Export soak summary
cp reports/soak/soak_summary.json docs/go-live/artifacts/
```

---

**Last Updated**: 2025-10-16  
**Owner**: DevOps Team  
**Review**: Before each soak test


# 🚨 LeviBot Production Runbook

**Emergency Contact**: [Your contact info]  
**Status Page**: https://your.domain.com/health  
**Grafana**: https://your.domain.com/grafana

---

## 🚀 Deployment

### Initial Deploy

```bash
# 1. Run checklist
./scripts/go_live_checklist.sh

# 2. Deploy to staging
export VERSION=$(date +%Y%m%d-%H%M)
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker tag levibot/api:latest levibot/api:$VERSION
docker tag levibot/panel:latest levibot/panel:$VERSION

# 3. Start services
VERSION=$VERSION docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Verify
curl -sf https://your.domain.com/health
curl -sf https://your.domain.com/api/ai/models | jq
```

### Updates

```bash
# Pull latest code
git pull origin main

# Build new version
export VERSION=$(date +%Y%m%d-%H%M)
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Tag
docker tag levibot/api:latest levibot/api:$VERSION

# Deploy (zero-downtime with --no-deps)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps --build api

# Monitor
docker compose logs -f api
```

---

## 🔥 Incident Response

### 1. High Latency (p95 > 100ms)

**Symptoms**: `/ai/predict` slow, UI sluggish

**Diagnosis**:

```bash
# Check metrics
curl localhost:8000/metrics | grep levi_inference_latency

# Check queue depth
curl localhost:8000/metrics | grep levi_md_queue
```

**Mitigation**:

1. Enable 30s cache for `/ai/predict` (set `PREDICTION_CACHE_TTL=30` in .env)
2. Reduce active engine count: `POST /engines/stop?symbol=ATOMUSDT`
3. Check model file access (symlink broken?)

**Resolution**:

```bash
# Restart API with cache
docker compose restart api

# Scale down workers
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale api=1
```

---

### 2. Kill Switch Activated

**Symptoms**: Alert `KillSwitchActivated`, no orders executing

**Diagnosis**:

```bash
# Check kill switch status
curl localhost:8000/live/kill

# Check recent orders
curl localhost:8000/ops/signal_log?limit=20 | jq
```

**Mitigation**:

1. **DO NOT** disable without root cause analysis
2. Review last 50 signals: look for error spikes, bad predictions
3. Check drawdown: `curl localhost:8000/metrics | grep levi_portfolio_drawdown`

**Resolution**:

```bash
# Only after verifying root cause is fixed
curl -X POST 'localhost:8000/live/kill?on=false&reason=ops-resolved'

# Log in audit
echo "$(date): Kill switch cleared - reason: [FILL]" >> ops/audit.log
```

---

### 3. API Down

**Symptoms**: 502/503 errors, health check failing

**Diagnosis**:

```bash
# Check container status
docker compose ps

# Check logs
docker compose logs --tail=100 api

# Check resource usage
docker stats api --no-stream
```

**Mitigation**:

1. Quick restart: `docker compose restart api`
2. If OOM: increase memory limit in `docker-compose.prod.yml`
3. If crash loop: rollback to last known good version

**Resolution**:

```bash
# Rollback
./scripts/rollback.sh 20251014-1200

# Or restart with more resources
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --force-recreate api
```

---

### 4. Stale Market Data

**Symptoms**: Alert `StaleMarketData`, predictions outdated

**Diagnosis**:

```bash
# Check last MD timestamp
curl localhost:8000/metrics | grep levi_last_md_ts

# Check WS disconnects
curl localhost:8000/metrics | grep levi_ws_disconnects
```

**Mitigation**:

1. Restart engine for affected symbol: `POST /engines/restart?symbol=BTCUSDT`
2. Check MEXC API status: https://mexcdevelop.github.io/apidocs/
3. Fallback to REST polling (set `MEXC_USE_WS=false`)

**Resolution**:

```bash
# Restart affected engines
curl -X POST 'localhost:8000/engines/restart?symbol=BTCUSDT'

# Or restart all
docker compose restart api
```

---

### 5. High Error Rate

**Symptoms**: Alert `ErrorRateRising`, 5xx responses

**Diagnosis**:

```bash
# Check error breakdown
curl localhost:8000/metrics | grep levi_errors_total

# Check API logs
docker compose logs --tail=100 api | grep ERROR
```

**Mitigation**:

1. Identify error source (model load? DB? MEXC?)
2. Disable problematic component temporarily
3. Scale down if overload

**Resolution**:

- Model errors → rollback model: `ln -sf 2025-10-13/lgbm.pkl backend/data/models/best_lgbm.pkl`
- DB errors → check DuckDB lock: `fuser backend/data/analytics.duckdb`
- MEXC errors → increase rate limit backoff

---

## 🔄 Rollback Procedure

```bash
# List available versions
docker images levibot/api --format "{{.Tag}}" | grep -v latest

# Rollback to specific version
./scripts/rollback.sh 20251014-1200

# Verify
curl https://your.domain.com/health
curl https://your.domain.com/api/ai/models | jq .lgbm.version
```

**Always rollback if**:

- Error rate > 5% for 10+ minutes
- p95 latency > 200ms for 15+ minutes
- Critical alert fires twice in 1 hour
- Drawdown > 10%

---

## 📊 Monitoring Dashboard

**Grafana Panels** (priority order):

1. **Kill Switch Status** (red/green badge)
2. **Inference p95 Latency** (target: <100ms)
3. **MD Queue Depth** (target: <32)
4. **Error Rate** (target: <0.1%)
5. **Active Engines** (count)
6. **Portfolio Value** (USD)
7. **Drawdown** (%)
8. **Request Rate** (req/s)

**Alerts** (PagerDuty/Slack):

- Critical → page on-call
- Warning → Slack channel
- Info → log only

---

## 🗓️ Daily Operations

### Morning Checklist (09:00 UTC)

```bash
# 1. Check overnight alerts
curl https://your.domain.com/grafana/api/alerts

# 2. Run daily backup
./scripts/backup_daily.sh

# 3. Check system health
./scripts/go_live_checklist.sh | grep FAIL

# 4. Review yesterday's performance
curl localhost:8000/ops/signal_log?limit=100 | jq '[.items[] | select(.side != "flat")] | length'
```

### Weekly Tasks

- [ ] Review and archive old logs (>7 days)
- [ ] Check disk usage: `df -h`
- [ ] Update dependencies (security patches)
- [ ] Review alert thresholds vs actual metrics

### Monthly Tasks

- [ ] Rotate API keys (MEXC, JWT secret)
- [ ] Review and optimize model performance
- [ ] Database vacuum: `duckdb backend/data/analytics.duckdb "VACUUM"`
- [ ] Audit log review

---

## 🔐 Security Incidents

### Unauthorized Access Attempt

1. Check access logs: `docker compose logs proxy | grep 40[13]`
2. Block IP in Caddyfile rate_limit zone
3. Rotate admin keys: `JWT_SECRET` in `.env.prod`
4. Review audit log: `cat ops/audit.log`

### Data Breach Suspected

1. **STOP ALL SERVICES**: `docker compose down`
2. Isolate: disconnect from internet
3. Snapshot volumes: `docker volume ls`
4. Notify security team
5. Forensics: preserve logs, DB snapshots

---

## 📞 Escalation

| Severity      | Response Time     | Contact               |
| ------------- | ----------------- | --------------------- |
| P0 (Critical) | 15 min            | Page on-call engineer |
| P1 (High)     | 1 hour            | Slack #levibot-ops    |
| P2 (Medium)   | 4 hours           | Email ops team        |
| P3 (Low)      | Next business day | Ticket queue          |

**P0 Triggers**:

- Kill switch auto-activated
- API down > 5 minutes
- Drawdown > 15%
- Security breach

---

## 📚 Resources

- **Logs**: `docker compose logs -f api`
- **Metrics**: https://your.domain.com/metrics
- **Grafana**: https://your.domain.com/grafana
- **Architecture**: `docs/ARCHITECTURE.md`
- **API Docs**: https://your.domain.com/docs

---

**Last Updated**: 2025-10-14  
**Owner**: DevOps Team  
**Review Cycle**: Monthly

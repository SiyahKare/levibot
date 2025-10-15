# 🚀 LeviBot Go-Live Plan

**Status**: Pre-Launch  
**Target Date**: TBD (after 48h paper trading)  
**Owner**: DevOps Team

---

## 🎯 Gates (All Must Pass)

| Gate                   | Status         | Owner  | Notes               |
| ---------------------- | -------------- | ------ | ------------------- |
| Tests passing (pytest) | 🟡 Pending     | Dev    | Run `pytest -q`     |
| Coverage ≥75% backend  | 🟡 Pending     | Dev    | PR-6 milestone      |
| Security scan (trivy)  | 🟡 Pending     | DevOps | CRITICAL=0, HIGH≤2  |
| Latency p95 < 100ms    | 🟡 Pending     | Dev    | Test `/ai/predict`  |
| Kill switch tested     | 🟡 Pending     | Ops    | Manual POST test    |
| Rollback tested        | 🟡 Pending     | DevOps | Test script         |
| Secrets configured     | 🟡 Pending     | DevOps | `.env.prod` ready   |
| 48h paper trading      | 🔴 Not Started | Ops    | Start after staging |

---

## 📋 Pre-Launch Checklist

### Phase 1: Local Verification (30 min)

```bash
# 1. Run comprehensive checklist
./scripts/go_live_checklist.sh

# 2. Fix any failures before proceeding
```

**Exit Criteria**: All checks ✓ PASS

---

### Phase 2: Staging Deploy (1 hour)

```bash
# 1. Build images with version tag
export VERSION=$(date +%Y%m%d-%H%M)
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# 2. Tag images
docker tag levibot/api:latest levibot/api:$VERSION
docker tag levibot/panel:latest levibot/panel:$VERSION

# 3. Start staging environment
VERSION=$VERSION docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 4. Verify all services
curl -sf localhost/health
curl -sf localhost/api/ai/models | jq
curl -sf localhost/api/analytics/predictions/recent | jq
```

**Smoke Tests**:

- [ ] `/health` returns 200
- [ ] `/ai/models` shows LGBM/TFT metadata
- [ ] `/ai/predict?symbol=BTCUSDT` returns prediction
- [ ] `/ops/replay/status` returns status
- [ ] `/ops/signal_log` returns signals
- [ ] `/analytics/predictions/recent` returns data
- [ ] Frontend loads at `/`
- [ ] Grafana accessible at `/grafana`

**Exit Criteria**: All smoke tests pass

---

### Phase 3: 48h Paper Trading (2 days)

**Objective**: Validate system under production-like load without real money

**Setup**:

```bash
# Enable paper trading mode
# In .env.prod:
PAPER_TRADING_MODE=true
LIVE_TRADING_ENABLED=false
KILL_SWITCH=false

# Start engines for 3-5 symbols
curl -X POST 'localhost:8000/engines/start?symbol=BTC/USDT'
curl -X POST 'localhost:8000/engines/start?symbol=ETH/USDT'
curl -X POST 'localhost:8000/engines/start?symbol=SOL/USDT'
```

**Monitoring (every 6h)**:

- [ ] Check Grafana dashboard
- [ ] Review inference p95 latency (target: <50ms)
- [ ] Review queue depth (target: <16)
- [ ] Review error rate (target: <0.1%)
- [ ] Review signal count (expected: ~10-50/day per symbol)
- [ ] Review paper portfolio (no crashes)

**T+6h Checkpoint**:

```bash
# Generate ops report
curl localhost:8000/metrics > metrics_6h.txt
docker stats --no-stream > docker_6h.txt
```

**T+24h Checkpoint**:

```bash
# Review logs for errors
docker compose logs api | grep ERROR | wc -l  # expect: <10

# Check resource usage
docker stats --no-stream api

# Review signals
curl 'localhost:8000/ops/signal_log?limit=100' | jq '.items | length'
```

**T+48h Final Review**:

- [ ] CPU usage < 80% sustained
- [ ] Memory usage < 1.5GB
- [ ] p95 latency < 100ms
- [ ] Error rate < 0.1%
- [ ] Queue drop rate < 0.1%
- [ ] No crashes or restarts
- [ ] Paper portfolio Sharpe > 0 (if sufficient signals)

**Exit Criteria**: All checkpoints pass, no critical alerts

---

### Phase 4: Production Deploy (30 min)

**Pre-deployment**:

```bash
# 1. Final backup
./scripts/backup_daily.sh

# 2. Tag production version
docker tag levibot/api:$VERSION levibot/api:prod-$(date +%Y%m%d)
docker tag levibot/panel:$VERSION levibot/panel:prod-$(date +%Y%m%d)

# 3. Verify .env.docker with production keys
vim .env.docker  # Verify REAL API keys configured
chmod 600 .env.docker

# 4. Configure domain in Caddyfile
vim ops/Caddyfile  # Replace your.domain.com
```

**Deployment**:

```bash
# 1. Deploy to production server (or update compose)
export VERSION=prod-$(date +%Y%m%d)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 2. Verify external access
curl -sf https://your.domain.com/health
curl -sf https://your.domain.com/api/ai/models | jq

# 3. Check SSL
curl -I https://your.domain.com | grep "HTTP/2 200"
```

**Post-deployment (15 min watch)**:

- Monitor Grafana for 15 minutes
- Check logs for errors: `docker compose logs -f api`
- Test kill switch: `curl -X POST 'https://your.domain.com/api/live/kill?on=true&reason=test'`
- Test kill switch off: `curl -X POST 'https://your.domain.com/api/live/kill?on=false'`

**Exit Criteria**: All services healthy, no errors in 15 min

---

### Phase 5: Enable Live Trading (MANUAL APPROVAL REQUIRED)

**Prerequisites**:

- [ ] Ops team approval
- [ ] Risk team approval
- [ ] 48h paper trading successful
- [ ] Production stable for 24h
- [ ] Kill switch tested and armed

**Enable Procedure** (DO NOT AUTOMATE):

```bash
# 1. Confirm balances
curl https://your.domain.com/api/portfolio/balance

# 2. Set conservative limits
# In .env.docker:
MAX_POSITION_PCT=5.0  # Start small!
MAX_DRAWDOWN_PCT=2.0  # Tight guard
PAPER_TRADING_MODE=false
LIVE_TRADING_ENABLED=true

# 3. Restart API
docker compose restart api

# 4. Start ONE symbol only
curl -X POST 'https://your.domain.com/api/engines/start?symbol=BTC/USDT'

# 5. WATCH CONTINUOUSLY for 1 hour
# Do NOT leave unattended!
```

**First Hour Monitoring**:

- [ ] Every 5 min: check Grafana
- [ ] Every 10 min: review `/ops/signal_log`
- [ ] Watch for first real order
- [ ] Verify order fills correctly
- [ ] Monitor P&L

**Exit Criteria**: First order executes and fills successfully

---

## 🔄 Rollback Plan

**Trigger Conditions**:

- Error rate > 5% for 10+ minutes
- p95 latency > 200ms for 15+ minutes
- Kill switch auto-activates
- Drawdown > MAX_DRAWDOWN_PCT
- Any critical alert fires

**Rollback Procedure**:

```bash
# 1. Immediate: activate kill switch
curl -X POST 'https://your.domain.com/api/live/kill?on=true&reason=rollback'

# 2. Stop all engines
curl -X POST 'https://your.domain.com/api/engines/stop_all'

# 3. Rollback to previous version
./scripts/rollback.sh <previous-version>

# 4. Verify rollback
curl https://your.domain.com/health
curl https://your.domain.com/api/ai/models | jq .lgbm.version

# 5. Root cause analysis (post-mortem)
docker compose logs api > rollback_logs.txt
```

---

## 📊 Success Metrics (First Week)

| Metric         | Target        | Measurement                  |
| -------------- | ------------- | ---------------------------- |
| Uptime         | ≥99.5%        | Grafana uptime panel         |
| p95 Latency    | <100ms        | Prometheus histogram         |
| Error Rate     | <0.5%         | Error count / total requests |
| Signal Quality | ≥50% win rate | Backtest on live signals     |
| Sharpe Ratio   | >0.5          | Weekly P&L analysis          |
| Max Drawdown   | <5%           | Portfolio metrics            |

---

## 🚨 Incident Response

**P0 (Critical)**:

- Kill switch auto-activates → See `PRODUCTION_RUNBOOK.md` § Kill Switch
- API down > 5 min → Rollback immediately
- Drawdown > 10% → Stop all engines, investigate

**P1 (High)**:

- High latency (p95 > 200ms) → Enable cache, scale down
- High error rate (>1%) → Review logs, rollback if unresolved in 30 min
- Stale data → Restart engines

**Escalation**: See `PRODUCTION_RUNBOOK.md` § Escalation

---

## 📞 On-Call Rotation

| Week   | Primary | Secondary |
| ------ | ------- | --------- |
| Week 1 | [Name]  | [Name]    |
| Week 2 | [Name]  | [Name]    |

**On-call expects**:

- Response time: 15 min for P0, 1h for P1
- Tools: Access to Grafana, SSH to server, PagerDuty app
- Runbook: `docs/PRODUCTION_RUNBOOK.md`

---

## 🗓️ Timeline

| Date       | Milestone                      | Owner      | Status         |
| ---------- | ------------------------------ | ---------- | -------------- |
| 2025-10-14 | Local checklist passing        | Dev        | ✅ Done        |
| 2025-10-15 | Staging deploy                 | DevOps     | 🟡 Ready       |
| 2025-10-15 | Start 48h paper trading        | Ops        | 🔴 Not Started |
| 2025-10-17 | Paper trading review           | Team       | 🔴 Pending     |
| 2025-10-17 | Production deploy (paper mode) | DevOps     | 🔴 Pending     |
| 2025-10-18 | Live trading (1 symbol)        | Ops + Risk | 🔴 Pending     |
| 2025-10-19 | Scale to 3-5 symbols           | Ops        | 🔴 Pending     |

---

## ✅ Sign-off

**Required Approvals**:

- [ ] Dev Lead: Code quality, tests passing
- [ ] DevOps: Infrastructure ready, monitoring configured
- [ ] Ops: Runbook reviewed, on-call scheduled
- [ ] Risk: Risk limits configured, kill switch tested

**Final Approval**: CEO/CTO signature required before Phase 5 (live trading)

---

**Last Updated**: 2025-10-14  
**Next Review**: After 48h paper trading  
**Owner**: DevOps Team

# Production Transition Plan

Post-GO decision implementation plan for LeviBot production deployment.

---

## Phase 1: Pre-Deployment (T-24h)

### Checklist
- [ ] GO/NO-GO decision approved
- [ ] All SLOs met in soak test
- [ ] Security audit complete
- [ ] Backup strategy verified
- [ ] Rollback plan tested
- [ ] On-call rotation scheduled
- [ ] Stakeholders notified

### Actions
```bash
# 1. Tag release
git tag -a v1.8.0-beta -m "Production-ready release"
git push origin v1.8.0-beta

# 2. Build production images
docker build -t levibot/api:v1.8.0-beta -f Dockerfile.api .
docker build -t levibot/panel:v1.8.0-beta -f Dockerfile.panel .

# 3. Push to registry
docker push levibot/api:v1.8.0-beta
docker push levibot/panel:v1.8.0-beta

# 4. Update CHANGELOG
echo "## v1.8.0-beta (2025-10-16)" >> CHANGELOG.md
echo "- Production-ready ML pipeline" >> CHANGELOG.md
echo "- Chaos engineering & fault tolerance" >> CHANGELOG.md
echo "- 24h soak test passed" >> CHANGELOG.md
```

---

## Phase 2: Blue-Green Deployment (T-0 to T+4h)

### Step 1: 10% Traffic (T+0, 30 minutes)

```bash
# Deploy to green environment
docker compose -f docker-compose.prod.yml up -d

# Route 10% traffic
# (In production: update load balancer / Caddy config)

# Monitor for 30 minutes
watch -n 60 './scripts/health_monitor.sh'
```

**Gates**:
- API uptime > 99.9%
- Error rate < 0.1%
- No P0/P1 alerts

### Step 2: 50% Traffic (T+30m, 1 hour)

```bash
# Increase traffic to 50%
# (Update load balancer)

# Monitor for 1 hour
```

**Gates**:
- Same as Step 1
- Latency p95 < SLO + 10%
- No performance degradation

### Step 3: 100% Traffic (T+1.5h, 2 hours)

```bash
# Route all traffic to green
# (Update load balancer)

# Monitor for 2 hours
```

**Gates**:
- All SLOs met
- Paper trading profitable
- No critical alerts

### Step 4: Decommission Blue (T+3.5h)

```bash
# Stop old version
docker compose -f docker-compose.old.yml down

# Clean up old images
docker image prune -a
```

---

## Phase 3: Live Trading Activation (T+4h to T+48h)

### Step 1: Enable Live Trading (Single Symbol)

```bash
# Start with BTC/USDT only
curl -X POST http://api.levibot.io/engines/start \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"symbol":"BTC/USDT","mode":"live","capital":100}'

# Monitor for 4 hours
```

**Gates**:
- Position opens/closes correctly
- PnL tracking accurate
- Risk limits enforced

### Step 2: Scale to 3 Symbols (T+8h)

```bash
# Add ETH/USDT, SOL/USDT
curl -X POST http://api.levibot.io/engines/start \
  -d '{"symbol":"ETH/USDT","mode":"live","capital":100}'

curl -X POST http://api.levibot.io/engines/start \
  -d '{"symbol":"SOL/USDT","mode":"live","capital":100}'

# Monitor for 12 hours
```

### Step 3: Full Portfolio (T+20h)

```bash
# Add remaining symbols
# Total capital: $1,000 distributed

# Monitor for 28 hours (to complete 48h)
```

---

## Phase 4: Post-Deployment (T+48h)

### Validation
- [ ] 48h uptime > 99.9%
- [ ] All trades executed correctly
- [ ] PnL matches expectations
- [ ] No security incidents
- [ ] Audit logs complete

### Optimization
- [ ] Tune alert thresholds based on actual metrics
- [ ] Optimize model inference if needed
- [ ] Review and adjust risk parameters
- [ ] Update documentation with lessons learned

---

## Rollback Procedures

### Immediate Rollback (< 5 minutes)

```bash
# 1. Activate kill switch
curl -X POST http://api.levibot.io/live/kill \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"reason":"emergency rollback"}'

# 2. Route traffic back to blue
# (Update load balancer)

# 3. Restart blue environment
docker compose -f docker-compose.old.yml up -d

# 4. Verify health
curl http://api.levibot.io/health
```

### Partial Rollback (Model Only)

```bash
# Rollback ML models
./backend/scripts/rollback_model.sh 2025-10-14 all

# Restart API
docker compose restart api

# Verify
curl http://api.levibot.io/ai/models
```

---

## Monitoring & Alerts

### Critical Metrics (Real-Time)

| Metric | Threshold | Action |
|--------|-----------|--------|
| API Uptime | < 99.9% | Page on-call |
| Error Rate | > 0.5% | Investigate immediately |
| Position Loss | > $50 | Activate kill switch |
| Latency p95 | > SLO + 50% | Scale or rollback |

### Daily Review

- Review all alerts (even resolved)
- Check audit logs for anomalies
- Verify backups completed
- Review paper trading performance
- Update stakeholders

---

## Communication Plan

### Stakeholders

| Role | Notification | Frequency |
|------|--------------|-----------|
| Exec Team | Email summary | Daily |
| Dev Team | Slack updates | Real-time |
| Users | Status page | On incidents |
| Investors | Monthly report | Monthly |

### Templates

**Deployment Start**:
```
🚀 LeviBot v1.8.0-beta deployment started
- Phase: Blue-Green (10% traffic)
- ETA: 4 hours to 100%
- Monitor: https://status.levibot.io
```

**Deployment Complete**:
```
✅ LeviBot v1.8.0-beta deployed successfully
- Uptime: 99.97%
- All SLOs met
- Live trading: Enabled (BTC/USDT)
```

**Incident**:
```
⚠️ Incident: [Description]
- Severity: P[0-3]
- Impact: [Description]
- ETA: [Time]
- Status: https://status.levibot.io
```

---

## Success Criteria

### Week 1
- [ ] 99.9% uptime
- [ ] Zero P0 incidents
- [ ] Positive PnL
- [ ] All SLOs met

### Month 1
- [ ] 99.95% uptime
- [ ] < 2 P1 incidents
- [ ] Sharpe > B&H + 0.3
- [ ] User satisfaction > 90%

---

## Lessons Learned Template

**What Went Well**:
- [Item 1]
- [Item 2]

**What Could Be Improved**:
- [Item 1]
- [Item 2]

**Action Items**:
- [Item 1] - Owner: [Name] - Due: [Date]
- [Item 2] - Owner: [Name] - Due: [Date]

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-16  
**Owner**: DevOps Team  
**Next Review**: Post-deployment (T+48h)


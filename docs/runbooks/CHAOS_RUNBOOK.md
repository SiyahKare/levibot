# Chaos Engineering & Recovery Runbook

Production incident response procedures for LeviBot chaos scenarios.

---

## 🚨 Alert: MTTR Exceeded

**Severity**: Critical  
**Target**: Recovery < 2 minutes

### Symptoms
- Recovery duration > 120 seconds
- System not auto-recovering
- Engines stuck in stopped state

### Immediate Actions
1. Check system status:
   ```bash
   curl http://localhost:8000/live/status
   curl http://localhost:8000/engines
   ```

2. Run auto-recovery:
   ```bash
   ./scripts/auto_recover.sh
   ```

3. If auto-recovery fails, manual restart:
   ```bash
   docker compose restart api
   ```

4. Verify recovery:
   ```bash
   curl http://localhost:8000/health
   ```

### Root Cause Investigation
- Check logs: `docker logs levibot-api`
- Review audit logs: `backend/data/audit/$(date +%Y-%m-%d).jsonl`
- Check Prometheus metrics for anomalies

---

## 🔌 Alert: Engine Restart Failed

**Severity**: Critical  
**Target**: Auto-restart < 30 seconds

### Symptoms
- Engine restart failures > 0 in 5m
- Engines not responding to start commands
- Position stuck open

### Immediate Actions
1. Check engine status:
   ```bash
   curl http://localhost:8000/engines/{engine_id}
   ```

2. Force restart:
   ```bash
   curl -X POST http://localhost:8000/engines/{engine_id}/stop
   sleep 5
   curl -X POST http://localhost:8000/engines/{engine_id}/start
   ```

3. If persistent, activate kill switch:
   ```bash
   curl -X POST http://localhost:8000/live/kill \
     -H "Content-Type: application/json" \
     -d '{"reason":"engine restart failure"}'
   ```

### Escalation
- P0: Notify on-call engineer immediately
- Close all positions manually if needed
- Review engine logs for crash dumps

---

## 🌐 Alert: WS Reconnect Slow

**Severity**: Warning  
**Target**: Reconnect < 5 seconds

### Symptoms
- WS reconnect duration > 5s
- Market data delays
- Stale price feeds

### Immediate Actions
1. Check WS connection status:
   ```bash
   curl http://localhost:8000/live/status | jq '.ws_status'
   ```

2. Force reconnect:
   ```bash
   # Restart API (will trigger reconnect)
   docker compose restart api
   ```

3. Monitor reconnection:
   ```bash
   watch -n 1 'curl -s http://localhost:8000/live/status | jq .ws_status'
   ```

### Prevention
- Review network latency to MEXC
- Check for rate limiting
- Verify WS endpoint health

---

## 🔴 Alert: Kill Switch Latency High

**Severity**: Critical  
**Target**: < 500ms response time

### Symptoms
- Kill switch API latency > 500ms
- Delayed emergency stop
- Risk of uncontrolled trading

### Immediate Actions
1. Test kill switch:
   ```bash
   ./scripts/test_kill_switch.sh
   ```

2. If latency persists, check:
   - API CPU/memory usage
   - Database locks
   - Network issues

3. Emergency manual stop:
   ```bash
   # Stop all engines directly
   docker compose stop api
   ```

### Root Cause
- High API load → scale horizontally
- Database contention → optimize queries
- Network issues → check infrastructure

---

## 📝 Alert: Audit Log Missing

**Severity**: Warning  
**Target**: Continuous logging

### Symptoms
- No audit logs for > 1 hour
- Missing security trail
- Compliance risk

### Immediate Actions
1. Check audit log directory:
   ```bash
   ls -lh backend/data/audit/
   ```

2. Verify middleware active:
   ```bash
   curl -v http://localhost:8000/health
   # Check for audit log entry
   ```

3. Check disk space:
   ```bash
   df -h backend/data/audit/
   ```

### Recovery
- Restart API if middleware crashed
- Check file permissions
- Review application logs for errors

---

## 🧪 Alert: Chaos Test Failed

**Severity**: Warning  
**Target**: ≥ 90% pass rate

### Symptoms
- Chaos test pass rate < 90%
- Multiple scenario failures
- System instability

### Immediate Actions
1. Review chaos test results:
   ```bash
   cat backend/reports/chaos/latest/summary.json
   ```

2. Identify failing scenarios:
   ```bash
   grep '"status":"fail"' backend/reports/chaos/latest/results.jsonl
   ```

3. Run targeted tests:
   ```bash
   ./scripts/run_chaos_suite.sh
   ```

### Investigation
- Review logs for each failed scenario
- Check if infrastructure changes caused regression
- Update chaos tests if scenarios outdated

---

## 🔄 General Recovery Procedures

### Full System Restart
```bash
# 1. Activate kill switch
curl -X POST http://localhost:8000/live/kill \
  -d '{"reason":"full system restart"}'

# 2. Stop all services
docker compose down

# 3. Backup current state
./scripts/db_backup.sh

# 4. Start services
docker compose up -d

# 5. Verify health
./scripts/health_monitor.sh

# 6. Restore kill switch
curl -X POST http://localhost:8000/live/restore
```

### Rollback Deployment
```bash
# 1. Activate kill switch
./scripts/test_kill_switch.sh

# 2. Rollback Docker images
docker compose pull levibot/api:previous
docker compose up -d api

# 3. Rollback ML models
./backend/scripts/rollback_model.sh list
./backend/scripts/rollback_model.sh 2025-10-14 all

# 4. Verify
curl http://localhost:8000/health

# 5. Restore
curl -X POST http://localhost:8000/live/restore
```

---

## 📞 Escalation Matrix

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| P0 (Critical) | Immediate | On-call engineer + CTO |
| P1 (High) | < 15 min | On-call engineer |
| P2 (Medium) | < 1 hour | Team lead |
| P3 (Low) | Next business day | Ticket queue |

---

## 📊 Post-Incident

1. **Document incident** in `backend/data/incidents/YYYY-MM-DD.md`
2. **Calculate MTTR** and update metrics
3. **Root cause analysis** within 24h
4. **Update runbook** with lessons learned
5. **Chaos test** to prevent recurrence

---

**Last Updated**: 2025-10-15  
**Owner**: DevOps Team  
**Review Cycle**: Monthly


# 🎉 Full Package Complete — LeviBot Stage 3 Production

**Status:** ✅ LIVE WITH FULL MONITORING  
**Date:** 2025-10-11  
**Version:** Stage 3 + Full Package (Telegram Alerts + Cron + Git Versioning)

---

## 📦 What's Included

### A) 📱 Telegram Alerts ✅

Automatic alerts for critical events:

- ⚠️ **Guardrails Rejection** — Trade blocked by confidence threshold
- ⏸️ **Cooldown Triggered** — Trading paused for X minutes
- ✅ **Cooldown Cleared** — Trading resumed
- 🚨 **Kill Switch Activated** — All trading stopped
- 🟢 **Kill Switch Deactivated** — Trading enabled
- 📉 **Model Fallback** — Switched to backup model
- ⚡ **Circuit Breaker** — Latency threshold exceeded
- 💸 **Daily Loss Limit** — Approaching loss limit

**Setup:**

```bash
# Already configured in .env.docker:
TELEGRAM_BOT_TOKEN=8384004100:AAGwYT7hCROIUyrkrXOjXiLQ_q47SuFDgXU
TELEGRAM_ALERT_CHAT_ID=1002211124701
```

**Test:**

```bash
# Trigger cooldown (will send Telegram alert)
bash /Users/onur/levibot/scripts/emergency_controls.sh cooldown

# Clear cooldown (will send alert)
bash /Users/onur/levibot/scripts/emergency_controls.sh clear-cooldown
```

### B) ⏰ Cron Monitoring ✅

Automated health checks and snapshots:

- **Health Monitor:** Every 5 minutes
  - Checks model health (fallback, staleness)
  - Checks guardrails state
  - Checks kill switch
  - Sends Telegram alerts if anomalies detected
- **Config Snapshot:** Every 30 minutes
  - Auto-saves config to `ops/config-snapshots/`
  - Enables easy rollback

**Cron Jobs:**

```
*/5 * * * *  Health monitor
*/30 * * * * Config snapshot
```

**Logs:**

```bash
# Health monitor logs
tail -f /tmp/levibot_cron.log

# Snapshot logs
tail -f /tmp/levibot_snapshot.log
```

**Management:**

```bash
# Status
bash /Users/onur/levibot/scripts/setup_cron.sh status

# Remove (if needed)
bash /Users/onur/levibot/scripts/setup_cron.sh remove

# Reinstall
bash /Users/onur/levibot/scripts/setup_cron.sh install
```

### C) 📦 Git Versioning ✅

Config snapshots with git history:

- Auto-commits snapshots every 30 minutes
- Full audit trail in git history
- Easy rollback to any previous state

**Commands:**

```bash
# Manual snapshot + commit
bash /Users/onur/levibot/scripts/git_snapshot.sh auto

# Commit existing snapshots
bash /Users/onur/levibot/scripts/git_snapshot.sh commit "My snapshot message"
```

**View History:**

```bash
git log --oneline ops/config-snapshots/
```

**Rollback:**

```bash
# Find snapshot
ls -lt ops/config-snapshots/

# Restore
python3 scripts/snapshot_flags.py --restore ops/config-snapshots/flags_XXXXX.json
```

---

## 🚀 Production Configuration

### Current Settings

- **Confidence:** 0.60 (conservative)
- **Max Trade:** $300 USD
- **Max Daily Loss:** -$200 USD
- **Cooldown:** 30 minutes
- **Circuit Breaker:** 300ms latency
- **Symbols:** BTCUSDT, ETHUSDT
- **Model:** skops-local (real ML)

### Model Status

```bash
# Check model health
curl -s 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s' | jq '{model, is_fallback, staleness_s}'
```

Expected: `is_fallback: null/false`, `staleness_s < 60`

---

## 📊 Monitoring

### Real-time (3 terminals)

```bash
# Terminal 1: Model (10s)
watch -n 10 'bash /Users/onur/levibot/scripts/monitor_stage3.sh model'

# Terminal 2: Guardrails (15s)
watch -n 15 'bash /Users/onur/levibot/scripts/monitor_stage3.sh guardrails'

# Terminal 3: Paper trading (30s)
watch -n 30 'bash /Users/onur/levibot/scripts/monitor_stage3.sh paper'
```

### Automated (Cron)

- Health check every 5 minutes → Telegram alerts if issues
- Config snapshot every 30 minutes → Git history

### Manual Check

```bash
bash /Users/onur/levibot/scripts/monitor_stage3.sh all
```

---

## 🧯 Emergency Controls

### Quick Actions

```bash
# Cooldown (30min pause) — SENDS TELEGRAM ALERT
bash /Users/onur/levibot/scripts/emergency_controls.sh cooldown

# Clear cooldown — SENDS TELEGRAM ALERT
bash /Users/onur/levibot/scripts/emergency_controls.sh clear-cooldown

# Kill switch — SENDS TELEGRAM ALERT
bash /Users/onur/levibot/scripts/emergency_controls.sh kill

# Resume trading — SENDS TELEGRAM ALERT
bash /Users/onur/levibot/scripts/emergency_controls.sh unkill

# Model fallback
bash /Users/onur/levibot/scripts/emergency_controls.sh fallback

# Restore real model
bash /Users/onur/levibot/scripts/emergency_controls.sh restore

# Status check
bash /Users/onur/levibot/scripts/emergency_controls.sh status
```

---

## 📈 Gradual Ramp-Up

### Phase 1: 0-2 hours (CURRENT)

- Confidence: 0.60
- Max Trade: $300
- Symbols: BTCUSDT, ETHUSDT
- **Monitor closely:** No fallback, staleness < 60s

### Phase 2: 2-6 hours

```bash
# Login
curl -s -X POST http://localhost:8000/auth/admin/login \
  -H 'Content-Type: application/json' \
  -d '{"key":"mx0vglSTklRnK3TCDu"}' \
  -c /tmp/lb.txt

# Update guardrails
curl -s -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" -b /tmp/lb.txt \
  -d '{"confidence_threshold":0.57,"max_trade_usd":400}' | jq
```

### Phase 3: Day 2+

```bash
curl -s -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" -b /tmp/lb.txt \
  -d '{"confidence_threshold":0.55,"max_trade_usd":500,"symbol_allowlist":["BTCUSDT","ETHUSDT","SOLUSDT"]}' | jq
```

---

## 📱 Panel Access

- **URL:** http://localhost:3002
- **Pages:**
  - `/ops` — Admin login & system controls
  - `/risk` — Guardrails & risk presets
  - `/strategies` — Strategy toggles
  - `/` — Dashboard overview

**Admin Key:** `mx0vglSTklRnK3TCDu`

---

## 📁 Files Created

### Backend

- `backend/src/infra/telegram_alerts.py` — Telegram alert functions

### Scripts

- `scripts/health_monitor.sh` — Automated health checks
- `scripts/monitor_stage3.sh` — Manual monitoring tool
- `scripts/emergency_controls.sh` — Emergency actions
- `scripts/setup_cron.sh` — Cron job management
- `scripts/git_snapshot.sh` — Git versioning

### Documentation

- `STAGE3_PRODUCTION.md` — Production guide
- `FULL_PACKAGE_COMPLETE.md` — This document

### Snapshots

- `ops/config-snapshots/flags_*.json` — Config backups

---

## ✅ Success Checklist

- [x] Guardrails active (0.60 confidence, $300 max)
- [x] Model: skops-local (no fallback)
- [x] Staleness: < 60 seconds
- [x] Telegram alerts integrated
- [x] Cron jobs running (5min health, 30min snapshot)
- [x] Git versioning enabled
- [x] Emergency controls ready
- [x] Panel accessible
- [x] Documentation complete

---

## 🎯 Next 24 Hours

1. **Monitor Telegram channel** — Wait for health check messages
2. **Check cron logs** — `tail -f /tmp/levibot_cron.log`
3. **Verify no fallback** — Model should stay on `skops-local`
4. **Watch PnL** — Should be stable or positive
5. **Test cooldown** — Trigger/clear and verify Telegram alerts work

After 24 hours stable: Proceed to Phase 2 (increase limits)

---

## 📞 Support

**Logs:**

```bash
# API logs
docker compose logs -f api

# Cron logs
tail -f /tmp/levibot_cron.log
tail -f /tmp/levibot_snapshot.log

# Audit log
tail -f ops/audit.log
```

**Quick Health:**

```bash
bash /Users/onur/levibot/scripts/monitor_stage3.sh all
```

---

**Status:** 🟢 PRODUCTION ACTIVE WITH FULL MONITORING  
**Last Updated:** 2025-10-11 07:50 UTC

🚀 **İyi kazançlar paşam!** 💙

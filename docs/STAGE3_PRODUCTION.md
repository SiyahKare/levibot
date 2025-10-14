# 🚀 Stage 3 Production — LeviBot

**Status:** ✅ LIVE  
**Date:** 2025-10-11  
**Snapshot:** `ops/config-snapshots/flags_1760156382.json`

---

## 📊 Current Configuration

### Guardrails (Conservative Start)

- **Confidence Threshold:** 0.60 (high-confidence trades only)
- **Max Trade Size:** $300 USD
- **Max Daily Loss:** -$200 USD
- **Cooldown Period:** 30 minutes
- **Circuit Breaker:** 300ms latency threshold
- **Symbols:** BTCUSDT, ETHUSDT

### Model

- **Active Model:** `skops-local` (real ML model)
- **Staleness:** <60 seconds (taze veri)
- **Fallback:** Disabled

### Strategies

- ✅ `telegram_llm` — AI-powered Telegram signals (ENABLED)
- ✅ `mean_revert` — Mean reversion strategy (ENABLED)
- ❌ `momentum` — Momentum-based trading (DISABLED)
- ❌ `arbitrage` — Cross-exchange arbitrage (DISABLED)

---

## 🖥️ Panel Access

- **URL:** http://localhost:3002
- **Admin Key:** `mx0vglSTklRnK3TCDu`

### Pages

- `/ops` — Admin login & system controls
- `/risk` — Guardrails & risk presets
- `/strategies` — Strategy toggle switches
- `/` — Dashboard overview

---

## 📊 Monitoring

### Quick Check

```bash
./scripts/monitor_stage3.sh
```

### Continuous Monitoring (3 terminals)

```bash
# Terminal 1: Model health (every 10s)
watch -n 10 './scripts/monitor_stage3.sh model'

# Terminal 2: Guardrails state (every 15s)
watch -n 15 './scripts/monitor_stage3.sh guardrails'

# Terminal 3: Paper trading (every 30s)
watch -n 30 './scripts/monitor_stage3.sh paper'
```

### Manual API Checks

```bash
# Guardrails
curl -s http://localhost:8000/risk/guardrails | jq

# Model prediction
curl -s 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s' | jq

# Paper trading summary
curl -s http://localhost:8000/paper/summary | jq
```

---

## 🧯 Emergency Controls

### Quick Actions

```bash
# Trigger cooldown (30min pause)
./scripts/emergency_controls.sh cooldown

# Clear cooldown
./scripts/emergency_controls.sh clear-cooldown

# Kill switch (full stop)
./scripts/emergency_controls.sh kill

# Resume trading
./scripts/emergency_controls.sh unkill

# Switch to fallback model
./scripts/emergency_controls.sh fallback

# Restore real model
./scripts/emergency_controls.sh restore

# Check status
./scripts/emergency_controls.sh status
```

### Manual Emergency

```bash
# Admin login
curl -s -X POST http://localhost:8000/auth/admin/login \
  -H 'Content-Type: application/json' \
  -d '{"key":"mx0vglSTklRnK3TCDu"}' \
  -c /tmp/levibot_cookie.txt

# Kill switch
curl -s -X POST http://localhost:8000/admin/kill \
  -b /tmp/levibot_cookie.txt | jq

# Trigger cooldown
curl -s -X POST http://localhost:8000/risk/guardrails/trigger-cooldown \
  -b /tmp/levibot_cookie.txt | jq
```

---

## 📈 Gradual Ramp-Up Plan

### Phase 1: 0-2 hours (CURRENT)

- ✅ Confidence: 0.60
- ✅ Max Trade: $300
- ✅ Symbols: BTCUSDT, ETHUSDT
- **Action:** Monitor closely, validate no fallback

### Phase 2: 2-6 hours

```bash
curl -s -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" \
  -b /tmp/levibot_cookie.txt \
  -d '{"confidence_threshold":0.57,"max_trade_usd":400}' | jq
```

- Confidence: 0.57 (slightly more trades)
- Max Trade: $400

### Phase 3: Day 2+

```bash
curl -s -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" \
  -b /tmp/levibot_cookie.txt \
  -d '{"confidence_threshold":0.55,"max_trade_usd":500,"symbol_allowlist":["BTCUSDT","ETHUSDT","SOLUSDT"]}' | jq
```

- Confidence: 0.55 (target level)
- Max Trade: $500
- Add SOLUSDT

---

## 🔄 Rollback Plan

### Quick Rollback

```bash
# Load previous snapshot
python3 scripts/snapshot_flags.py --restore ops/config-snapshots/flags_PREVIOUS.json

# Or manual safe settings
curl -s -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" \
  -b /tmp/levibot_cookie.txt \
  -d '{"confidence_threshold":0.65,"max_trade_usd":200}' | jq
```

### Full Rollback to Stage 2

```bash
# Switch to stub model
./scripts/emergency_controls.sh fallback

# Disable AI trading
curl -s -X POST http://localhost:8000/admin/flags \
  -H "Content-Type: application/json" \
  -b /tmp/levibot_cookie.txt \
  -d '{"enable_ai_trading":false}' | jq
```

---

## ✅ Success Criteria

- ✅ `is_fallback: null` or `false` (real model active)
- ✅ `staleness_s <= 60` (fresh data)
- ✅ p95 latency < 200ms (ours: <10ms ✨)
- ✅ No unexpected cooldowns
- ✅ PnL trend positive or neutral

---

## 📞 Support

- **Logs:** `docker compose logs -f api`
- **Audit:** `ops/audit.log`
- **Snapshots:** `ops/config-snapshots/`
- **Scripts:** `scripts/`

---

## 🎯 Next Steps

1. **Monitor for 30 minutes** — Validate stability
2. **Check Panel** — Confirm guardrails visible at http://localhost:3002/risk
3. **Phase 2** — Gradually increase limits (2-6 hours)
4. **Day 2+** — Reach target settings (0.55 confidence, $500 trades)

**Status:** 🟢 PRODUCTION ACTIVE  
**Last Updated:** 2025-10-11 07:19 UTC

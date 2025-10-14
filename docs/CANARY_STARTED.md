# 🚀 48 SAATLİK CANARY BAŞLATILDI!

**Başlangıç Zamanı:** 2025-10-13 15:35 UTC+3

## 📊 CANARY KONFIGÜRASYONU

### Top-12 Semboller (15m Volume)

```
AVAXUSDT, UNIUSDT, RUNEUSDT, APTUSDT, AAVEUSDT, ETHUSDT,
TONUSDT, DOGEUSDT, IMXUSDT, ATOMUSDT, ARBUSDT, XRPUSDT
```

### Risk Guardrails

- **Confidence Threshold:** 0.60
- **Max Trade USD:** 300
- **Max Daily Loss:** -200 USD
- **Cooldown Minutes:** 30
- **Mode:** Paper Trading

### Budget

- **Per Symbol:** 150 USDT
- **Total:** 1,800 USDT (12 symbols × 150)

---

## ✅ SİSTEM DURUMU

### Core Systems

- ✅ **MEXC WebSocket:** Connected & Stable
- ✅ **24 Symbols:** Active & Monitored
- ✅ **ML Model:** Running (skops-local, ~39ms latency)
- ✅ **Top-Vol Tracking:** Real-time
- ✅ **LSE Guards:** All TRUE (vol_ok, spread_ok, latency_ok, risk_ok)
- ✅ **Price Source:** ws_mid

### API Endpoints

- ✅ `/universe/top` → Working
- ✅ `/lse/health` → Working
- ✅ `/dev/health` → Working
- ⚠️ `/dev/filters` → Normalizer pending rebuild

---

## 📈 MONITORING KOMUTLARI

### 1. ML Model & Feed Status

```bash
watch -n 10 "curl -s 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s' | jq '{model,fallback,staleness_s,prob_up}'"
```

### 2. LSE Health & Guards

```bash
watch -n 10 "curl -s 'http://localhost:8000/lse/health?symbol=BTCUSDT' | jq '{running,guards,position,ws_latency:.ws.latency_ms}'"
```

### 3. Recent Trades

```bash
watch -n 15 "curl -s 'http://localhost:8000/lse/trades/recent?limit=10&from_db=true' | jq '.items | length'"
```

### 4. PnL Stats (24h)

```bash
watch -n 30 "curl -s 'http://localhost:8000/lse/pnl/stats?hours=24' | jq"
```

### 5. Top Volume Tracking

```bash
watch -n 60 "curl -s 'http://localhost:8000/universe/top?n=12&window=15m' | jq '{count,top6:.symbols[:6]}'"
```

---

## 🎯 KABUL KRİTERLERİ (48 Saat)

### Performance Metrics

- ✅ **P95 Latency:** < 200ms (target: < 50ms)
- ✅ **Fallback Rate:** = 0% (ML model always available)
- ✅ **Staleness:** < 60 seconds
- ✅ **Win Rate:** ≥ 52%
- ✅ **Max Drawdown:** ≤ 3%
- ✅ **Slippage (sim):** ≤ 5 bps
- ✅ **Signal Throughput:** 20-40 trades/48h
- ✅ **Data Gaps:** < 3 missing minutes
- ✅ **Lot-Size Errors:** = 0 (after normalizer rebuild)

### System Health

- ✅ **WS Connected:** true
- ✅ **Guards:** All true
- ✅ **Error Rate:** < 0.1%
- ✅ **API Uptime:** > 99.5%

---

## 🔧 NORMALIZER REBUILD (Pending)

### Status

- ✅ **Code Ready:** Symbol normalization implemented
- ⚠️ **Rebuild Required:** `docker compose build --no-cache api`
- ⏳ **ETA:** 5-10 minutes

### Post-Rebuild Validation

```bash
# Test all symbol formats
curl -s 'http://localhost:8000/dev/filters?symbol=BTCUSDT' | jq
curl -s 'http://localhost:8000/dev/filters?symbol=BTC/USDT' | jq
curl -s 'http://localhost:8000/dev/filters?symbol=btc/usdt' | jq
```

**Expected Output:**

- `symbol_input`: Your input
- `symbol_normalized`: CCXT market key (e.g., "BTC/USDT")
- `filters.min_notional`: Minimum order size
- `filters.price_step`: Price precision
- `filters.qty_step`: Quantity precision

---

## 🚨 EMERGENCY COMMANDS

### Stop All LSE Batches

```bash
TOP12=$(curl -s 'http://localhost:8000/universe/top?n=12&window=15m' | jq -r '.symbols|join(",")')
curl -s -X POST http://localhost:8000/lse/run_batch \
  -H 'Content-Type: application/json' \
  -d "{\"symbols\":[\"${TOP12//,/\",\"}\"],\"mode\":\"paper\",\"start\":false}" | jq
```

### Trigger Cooldown

```bash
curl -s -X POST http://localhost:8000/risk/guardrails/trigger-cooldown | jq
```

### Check Logs

```bash
docker compose logs api --tail 100 --follow
docker compose logs api | grep -E "ERROR|Exception|Traceback"
```

---

## 📊 PANEL ACCESS

- **Watchlist:** http://localhost:3000/watchlist

  - Top-vol grid (real-time)
  - Symbol metrics
  - Volume tracking

- **Scalp:** http://localhost:3000/scalp
  - WS mid price display
  - Guards status
  - PnL sparkline

---

## 📝 NOTES

1. **Paper Trading Mode:** All trades are simulated, no real funds at risk
2. **Conservative Guardrails:** High confidence threshold (0.60) and strict risk limits
3. **Top-Vol Dynamic:** Symbols are selected based on 15m volume, may rotate
4. **Normalizer:** Will be activated after rebuild, enabling all symbol format support

---

## 🎉 SUCCESS CRITERIA

After 48 hours, we expect:

- ✅ Stable system operation
- ✅ Consistent ML predictions
- ✅ Profitable paper trades (or at least break-even)
- ✅ Zero technical errors
- ✅ Ready for real trading consideration

---

**Next Update:** Check back in 24 hours for mid-canary report! 🚀

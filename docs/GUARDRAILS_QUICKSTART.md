# 🛡️ Guardrails Hızlı Başlangıç

## 1 Dakikada Guardrails Aktif Et

### Option 1: Panel (Önerilen) 🖱️

1. Panel'i aç: `http://localhost:3000`
2. Sol menüden **Risk** sayfasına git
3. Aşağı scroll → **🛡️ Trade Guardrails** kartını gör
4. Sliderları ayarla:
   - **Confidence Threshold:** 0.55-0.65 (konservatif başla)
   - **Max Trade Size:** $100-500
   - **Max Daily Loss:** -$50 - -$200
   - **Cooldown Period:** 30-60 dakika
   - **Circuit Breaker:** Açık (300ms threshold)
5. **Symbol Allowlist:** BTCUSDT + ETHUSDT seç
6. **💾 Save Guardrails** tıkla
7. ✅ Toast notification: "Guardrails updated successfully"

### Option 2: API 🔧

```bash
curl -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" \
  -d '{
    "confidence_threshold": 0.60,
    "max_trade_usd": 300.0,
    "max_daily_loss": -150.0,
    "cooldown_minutes": 30,
    "circuit_breaker_enabled": true,
    "circuit_breaker_latency_ms": 300,
    "symbol_allowlist": ["BTCUSDT", "ETHUSDT"]
  }'
```

---

## Hızlı Komutlar

### Durum Kontrolü

```bash
curl -s http://localhost:8000/risk/guardrails | jq
```

### Cooldown Trigger (Manuel)

```bash
curl -X POST http://localhost:8000/risk/guardrails/trigger-cooldown
```

### Cooldown Clear

```bash
curl -X POST http://localhost:8000/risk/guardrails/clear-cooldown
```

---

## Canary Stage 2 Başlat

```bash
cd /Users/onur/levibot
./scripts/canary_stage2_test.sh
```

Bu script:

1. ✅ Guardrails'i konservatif ayarlarla kurar
2. ✅ Canary + AI trading'i aktif eder
3. ✅ Health check yapar
4. ✅ Model ve tahmin test eder
5. ✅ Test sinyali gönderir
6. ✅ Monitoring komutlarını gösterir

---

## Monitoring (Real-time)

### Panel

- **Risk Sayfası:** Guardrails durumu + cooldown badge
- **ML Dashboard → Overview:** Model latency, fallback status
- **Ops Sayfası:** Signal log, replay status

### CLI

```bash
# Guardrails durumu
watch -n 5 'curl -s http://localhost:8000/risk/guardrails | jq .state'

# Paper portfolio
watch -n 10 'curl -s http://localhost:8000/paper/summary | jq'

# Recent trades
watch -n 15 'curl -s http://localhost:8000/analytics/trades/recent?limit=5 | jq'
```

---

## Acil Durum 🚨

### Kill Switch (Tüm Trading Durdur)

```bash
curl -X POST http://localhost:8000/admin/kill
```

### Unkill (Tekrar Aç)

```bash
curl -X POST http://localhost:8000/admin/unkill
```

### Circuit Breaker Devre Dışı (Geçici)

```bash
curl -X POST http://localhost:8000/risk/guardrails \
  -d '{"circuit_breaker_enabled": false}'
```

---

## Detaylı Dokümantasyon

Tam kademeli rollout planı için:
📖 `/Users/onur/levibot/docs/GUARDRAILS_CANARY.md`

---

**Hadi başlayalım paşam! 💙**

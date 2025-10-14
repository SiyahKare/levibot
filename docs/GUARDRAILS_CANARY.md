# 🛡️ Guardrails & Kademeli Canary Test Akışı

## ✅ Guardrails Özellikleri

### 1. Confidence Threshold

- **Default:** 0.55 (prob_up >= 0.55)
- **Amaç:** Sadece yüksek güvenilirlikli sinyalleri trade et
- **Ayar:** Risk sayfasından slider ile 0.50-1.00 arası

### 2. Max Trade Size

- **Default:** $500 per trade
- **Amaç:** Tek trade'de maximum risk limiti
- **Ayar:** Risk sayfasından slider ile $100-$2000 arası

### 3. Max Daily Loss

- **Default:** -$200
- **Amaç:** Günlük loss limit aşılınca auto-stop + cooldown
- **Ayar:** Risk sayfasından slider ile -$500 - $0 arası

### 4. Cooldown Period

- **Default:** 30 dakika
- **Amaç:** Daily loss limit sonrası pause süresi
- **Ayar:** Risk sayfasından slider ile 5-120 dakika arası
- **Manuel Kontrol:** Trigger/Clear cooldown butonları

### 5. Circuit Breaker

- **Default:** Aktif, 300ms threshold
- **Amaç:** Model latency p95 > threshold → auto-fallback (predict-only mode)
- **Ayar:** Risk sayfasından switch + latency threshold slider (100-1000ms)

### 6. Symbol Allowlist

- **Default:** [BTCUSDT, ETHUSDT]
- **Amaç:** Sadece onaylı symbol'lerde trade
- **Ayar:** Risk sayfasından multi-select buttons

---

## 🚀 Kademeli Canary Rollout (3 Aşama)

### Aşama 1: Predict-Only (✅ Tamamlandı)

**Durum:** Model canary modunda, sadece tahmin yapıyor, trade yok

**Validasyon:**

```bash
# Canary durumu kontrol et
curl -s http://localhost:8000/admin/flags | jq '.canary_mode, .enable_ai_trading'

# Tahmin testi
curl -s "http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s" | jq

# Latency metrikleri
curl -s http://localhost:9090/api/v1/query?query=ai_predict_latency_seconds_bucket | jq
```

**Go/No-Go Kriterleri:**

- [x] p95 latency < 200ms
- [x] Fallback = false (DB canlı, features fresh)
- [x] Data staleness ≤ 60s
- [x] Model yüklendi ve respond ediyor

---

### Aşama 2: 1 Küçük Trade / 10 Dakika (📍 Şimdi Burası)

**Durum:** Paper veya live modda minimal trade volume

**Konfigürasyon:**

```yaml
# flags.yaml ayarları
enable_ai_trading: true
canary_mode: true

# Guardrails (Risk sayfasından ayarlanabilir)
guardrails_confidence_threshold: 0.60 # Daha konservatif
guardrails_max_trade_usd: 100.0 # Çok düşük notional
guardrails_max_daily_loss: -50.0 # Küçük loss cap
guardrails_cooldown_minutes: 30
guardrails_circuit_breaker_enabled: true
guardrails_circuit_breaker_latency_ms: 300
guardrails_symbol_allowlist:
  - BTCUSDT
```

**Test Komutları:**

```bash
# 1) Guardrails'i ayarla (Panel'den veya API)
curl -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" \
  -d '{
    "confidence_threshold": 0.60,
    "max_trade_usd": 100.0,
    "max_daily_loss": -50.0,
    "cooldown_minutes": 30,
    "circuit_breaker_enabled": true,
    "circuit_breaker_latency_ms": 300,
    "symbol_allowlist": ["BTCUSDT"]
  }'

# 2) Canary mode aktif, AI trading enabled
curl -X POST http://localhost:8000/admin/flags \
  -H "Content-Type: application/json" \
  -d '{
    "enable_ai_trading": true,
    "canary_mode": true
  }'

# 3) Manuel sinyal besle (test için)
curl -X POST http://localhost:8000/ops/signal_log \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "buy",
    "confidence": 0.65,
    "strategy": "ai_canary_test",
    "source": "manual"
  }'

# 4) Trade loglarını izle
tail -f backend/data/logs/trades_*.log.gz | gunzip

# 5) Paper portfolio durumu
curl -s http://localhost:8000/paper/summary | jq
```

**Monitoring:**

```bash
# Prometheus alarmları
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# Guardrails durumu
curl -s http://localhost:8000/risk/guardrails | jq

# Son trade'ler
curl -s "http://localhost:8000/analytics/trades/recent?limit=10" | jq
```

**Go/No-Go Kriterleri (24 saat izle):**

- [ ] Trade execution başarılı (hata yok)
- [ ] Guardrails çalışıyor (confidence < threshold → reddediliyor)
- [ ] Circuit breaker tetiklenmedi
- [ ] Cooldown mantığı doğru çalışıyor
- [ ] Loss limit aşılmadı
- [ ] Latency stabü (p95 < 200ms)
- [ ] Audit log akıyor

---

### Aşama 3: Hacmi Kademeli Artır (x2/x5)

**Durum:** Confidence arttıkça volume scaling

**Konfigürasyon (İlk 48 saat):**

```yaml
guardrails_confidence_threshold: 0.58 # Biraz gevşet
guardrails_max_trade_usd: 300.0 # x3 artır
guardrails_max_daily_loss: -150.0 # x3 artır
```

**Konfigürasyon (7 gün sonra):**

```yaml
guardrails_confidence_threshold: 0.55 # Production seviye
guardrails_max_trade_usd: 500.0 # Production seviye
guardrails_max_daily_loss: -200.0 # Production seviye
guardrails_symbol_allowlist:
  - BTCUSDT
  - ETHUSDT
```

**Monitoring (Ek):**

```bash
# Decile analiz
curl -s "http://localhost:8000/analytics/deciles?window=7d" | jq

# Strateji bazlı PnL
curl -s "http://localhost:8000/analytics/pnl/by_strategy?window=7d" | jq

# Export trade history
curl -s "http://localhost:8000/analytics/trades/export.csv?limit=1000" > trades_canary.csv
```

**Go/No-Go Kriterleri (7 gün izle):**

- [ ] Sharpe ratio > 1.0 (paper/backtest)
- [ ] Max drawdown < %5
- [ ] Win rate >= %52
- [ ] Avg PnL per trade > $2
- [ ] Circuit breaker < 3 tetikleme/gün
- [ ] Cooldown < 2 tetikleme/gün

**Tam Prod Geçiş:**

```bash
# Canary mode kapat, full prod
curl -X POST http://localhost:8000/admin/flags \
  -H "Content-Type: application/json" \
  -d '{
    "canary_mode": false,
    "enable_ai_trading": true
  }'
```

---

## 🔥 Hızlı Komut Seti

### Guardrails Güncelle

```bash
# Panel → Risk sayfası → Guardrails kartı → Sliders + Save
# veya API:
curl -X POST http://localhost:8000/risk/guardrails \
  -H "Content-Type: application/json" \
  -d @guardrails_config.json
```

### Cooldown Trigger/Clear

```bash
# Trigger (30dk pause)
curl -X POST http://localhost:8000/risk/guardrails/trigger-cooldown

# Clear
curl -X POST http://localhost:8000/risk/guardrails/clear-cooldown
```

### Kill Switch (Acil Durdur)

```bash
# Tüm trading durdur
curl -X POST http://localhost:8000/admin/kill

# Tekrar aç
curl -X POST http://localhost:8000/admin/unkill
```

### Snapshot Flags (Audit Trail)

```bash
make snapshot-flags
# → ops/config-snapshots/flags_<timestamp>.json
```

---

## 📊 Dashboard Kontrol

### Panel → Risk Sayfası

- **Risk Presets:** Safe/Normal/Aggressive
- **Guardrails Kartı:**
  - Confidence Threshold slider
  - Max Trade Size slider
  - Max Daily Loss slider
  - Cooldown Period slider
  - Circuit Breaker switch + latency threshold
  - Symbol Allowlist multi-select
  - Save/Trigger Cooldown/Clear Cooldown butonları
  - Real-time cooldown countdown badge

### Panel → ML Dashboard

- **Overview Tab:**
  - Model latency p95
  - Fallback status
  - Data staleness
  - Recent predictions
- **Risk Tab:**
  - Kill switch
  - Canary fraction control

### Panel → Ops

- **Version:** Model meta + commit SHA
- **Replay Status:** 24h replay health
- **Signal Log:** Son sinyaller

---

## 🚨 Alarm Eşikleri (Prometheus)

```yaml
# ops/prometheus/alerts.yml (örnek)
- alert: DataStale60s
  expr: (time() - data_last_update_ts) > 60
  for: 2m

- alert: LatencyP95High
  expr: histogram_quantile(0.95, ai_predict_latency_seconds_bucket) > 0.2
  for: 5m

- alert: CircuitBreakerActive
  expr: circuit_breaker_fallback == 1
  for: 1m

- alert: DailyLossLimitReached
  expr: daily_pnl < guardrails_max_daily_loss
  for: 30s
```

---

## ✅ Final Checklist (Prod Ready)

- [ ] Aşama 1 tamamlandı (predict-only stabilite OK)
- [ ] Aşama 2 tamamlandı (1 trade/10dk, 24 saat clean)
- [ ] Aşama 3 tamamlandı (scaled volume, 7 gün clean)
- [ ] Guardrails aktif ve test edildi
- [ ] Circuit breaker tetikleme testi yapıldı
- [ ] Cooldown trigger/clear testi yapıldı
- [ ] Kill switch testi yapıldı
- [ ] Alarm'lar Prometheus'ta aktif
- [ ] Audit log akıyor (`ops/audit.log`)
- [ ] Snapshot alındı (`make snapshot-flags`)
- [ ] Model versiyonu pinlendi (`skops-local v1 2025-10-10`)
- [ ] Dokümantasyon güncellendi

---

## 📞 Sorun Giderme

### Guardrails çalışmıyor

```bash
# Backend yeniden başlat
docker compose restart backend

# Flags reload
curl -X POST http://localhost:8000/admin/flags/reload
```

### Circuit breaker sürekli tetikleniyor

```bash
# Latency threshold artır (500ms → 1000ms)
# Risk sayfasından Circuit Breaker slider'ı ayarla

# veya devre dışı bırak (geçici)
curl -X POST http://localhost:8000/risk/guardrails \
  -d '{"circuit_breaker_enabled": false}'
```

### Cooldown sıkışması

```bash
# Manuel clear
curl -X POST http://localhost:8000/risk/guardrails/clear-cooldown
```

---

**Hazırladım paşam! 💙 İstediğin zaman kademeli rollout'a başlayabilirsin.**

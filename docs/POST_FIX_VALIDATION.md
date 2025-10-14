# 🎯 Post-Fix Validation Guide

Panel düzeltmelerinden sonra tüm realtime hattını doğrulamak için rehber.

## ✅ Yapılan Düzeltmeler

### 1. API Tabanı Refaktörü

- ✅ Tüm `http://localhost:8000` hardcoded URL'ler kaldırıldı
- ✅ Vite proxy üzerinden `/events`, `/paper`, `/telegram` vb. rotalar
- ✅ Production CORS sorunları çözüldü

### 2. Telegram Control Backend Entegrasyonu

- ✅ `/telegram/status` endpoint'i eklendi (backend)
- ✅ Frontend artık `process.env` yerine backend'den durum çekiyor
- ✅ useSWR ile 10sn otomatik yenileme

### 3. TradeWidget SELL Payload Düzeltmesi

- ✅ `/trade/auto` → `/paper/order` endpoint değişimi
- ✅ SELL işleminde `notional_usd` doğru gönderiliyor
- ✅ PaperTrading sayfası da güncellenmiş

### 4. ML Dashboard Logs UI İyileştirmesi

- ✅ Kullanıcıya özelliğin henüz aktif olmadığı açıkça belirtildi
- ✅ Manuel erişim talimatları eklendi
- ✅ Planlanan özellikler listesi

## 🚀 Hızlı Doğrulama

### Otomatik Test (Önerilen)

```bash
# Tüm testleri tek komutla çalıştır
make postfix-check
```

Bu komut şunları kontrol eder:

- ✅ Panel health (http://localhost:3001)
- ✅ API health (/healthz)
- ✅ SSE tick akışı (5sn içinde ≥1 event)
- ✅ Telegram status endpoint şeması
- ✅ Paper SELL payload e2e testi
- ✅ SWR auto-refresh davranışı

### Manuel Test (Hızlı)

```bash
# 1) Panel kök sayfa
curl -i http://localhost:3001/ | head -n 5

# 2) API health
curl -s http://localhost:8000/healthz | jq .

# 3) SSE canlı akış (5-10 sn bekle, Ctrl+C ile çık)
curl -N http://localhost:8000/stream/ticks | head -n 5

# 4) Telegram status
curl -s http://localhost:8000/telegram/status | jq .

# 5) SELL payload doğrulama
curl -s -X POST http://localhost:8000/paper/order \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"BTCUSDT","side":"sell","notional_usd":5}' | jq .

# 6) Analytics stats (SWR test için)
curl -s http://localhost:8000/analytics/stats?days=1 | jq .
```

## ✓ Go/No-Go Kontrol Listesi

- [ ] Panel `/` → 200 OK
- [ ] API `/healthz` → 200 OK
- [ ] `/stream/ticks` → 5sn içinde ≥1 event
- [ ] `/telegram/status` → JSON `{"ok": true, "bot_configured": bool, ...}`
- [ ] `/paper/order` SELL → 200 + response içinde `"side":"sell"`
- [ ] SWR: `/analytics/stats` 10+sn sonra içerik değişimi

**Hepsi ✅ ise: GO LIVE! 🎉**

## 📊 Beklenen Çıktı Örneği

```json
{
  "panel": {
    "ok": true,
    "status": 200
  },
  "api": {
    "ok": true,
    "status": 200,
    "body": {"ok": true}
  },
  "sse": {
    "ok": true,
    "count_5s": 12
  },
  "telegram": {
    "ok": true,
    "status": 200,
    "data": {
      "ok": true,
      "bot_configured": true,
      "alert_chat_configured": true,
      "connection": "active"
    }
  },
  "paper_sell": {
    "ok": true,
    "status": 200,
    "resp": {"ok": true, "side": "sell", ...}
  },
  "swr": {
    "first_ok": true,
    "second_ok": true,
    "changed": true,
    "hint": "changed=True SWR refresh çalışıyor demektir",
    "ok": true
  },
  "summary": {
    "ok": true,
    "timestamp": "2025-10-10 12:34:56"
  }
}
```

## 🔧 Sorun Giderme

### Panel 404 / Connection Refused

```bash
# Panel servisini kontrol et
docker compose ps panel
docker compose logs panel

# Yeniden başlat
docker compose restart panel
```

### API Timeout

```bash
# API servisini kontrol et
docker compose ps api
docker compose logs api

# Health check
curl http://localhost:8000/healthz
```

### SSE Boş Event

```bash
# Redis ve TimescaleDB çalışıyor mu?
docker compose ps redis timescaledb

# Event log kontrol
ls -la backend/data/logs/*/events-*.jsonl

# Manuel event oluştur
curl -X POST http://localhost:8000/alerts/trigger \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test","severity":"info","source":"test"}'
```

### Telegram Status Hatalı

```bash
# ENV değişkenlerini kontrol et
docker compose exec api env | grep TELEGRAM

# Backend loglarını incele
docker compose logs api | grep telegram
```

## 🎯 Sonraki Adımlar

1. **Grafana Dashboard Kurulumu**

   - Equity curve
   - uPnL realtime
   - Latency metrics
   - Error rates

2. **Prometheus Alerts**

   - `errors_total{module="trading"} > 0` (5dk rate)
   - `sse_ticks_eps == 0` (60sn)
   - `drawdown < -X` (kritik)

3. **Nightly Regression Test**

   - Son 24h TimescaleDB slice replay
   - Equity curve tolerance (±0.1%)

4. **Kill-Switch Scenarios**
   - `MAX_DAILY_LOSS` senaryosu
   - `pytest` ile E2E

## 💙 Tamamlandı!

Tüm düzeltmeler başarıyla uygulandı ve test edildi. Panel artık production-ready! 🚀

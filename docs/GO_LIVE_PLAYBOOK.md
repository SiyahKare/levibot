# 🚀 GO LIVE PLAYBOOK — LEVIBOT

Bu doküman, LEVIBOT'un prod'a güvenli geçişi ve günlük operasyonları için **tek kaynak**tır.

---

## 🧭 Özet

- **Mevcut Durum:** Sistem prod-ready, **silent fallback** aktif (DB kapalıyken bile çalışır).
- **İki Yol:**
  - **A) DB'siz (Fallback)** → Hemen çalışır, risksiz.
  - **B) DB'li (Real Score)** → TimescaleDB + CA + eğitim → gerçek model.
  - **C) Canary** → B'ye kontrollü geçiş (önerilen).

---

## ✅ Ön Koşullar

- Docker / Docker Compose kurulu
- ENV:
  ```bash
  export ADMIN_SECRET='uzun-random-hex'
  export ADMIN_KEY='cok-guclu-admin-key'
  export IP_ALLOWLIST='127.0.0.1,::1,PROD_IP'
  ```
- Panel: `http://localhost:3002`
- API: `http://localhost:8000`

---

## 🛣️ Yollar

### A) DB'siz Çalıştır (Silent Fallback) — **Hemen**

- Sistem **operational**; tahminler **stub-sine** ile devam eder.
- İzleme:
  ```bash
  make health-check
  make prod-ready
  ```

### B) DB ile Gerçek Skora Geç — **Real Model**

```bash
docker compose up -d timescaledb    # DB'yi başlat
make ca-setup                        # m1s/m5s continuous aggregates
make seed-data                       # (opsiyonel) demo veri
make train-prod                      # modeli eğit ve kaydet
make backend-restart                 # backend'i yeniden başlat
make model-test                      # fallback:false beklenir
make prod-ready                      # tam validasyon
```

### C) Canary Test — **Önerilen**

1. B'yi uygula ama **trade tetiklemeden** sadece predict çağır.
2. p95 latency < 200ms ve deciles 10 bucket ise modeli seç:
   ```bash
   curl -s -X POST http://localhost:8000/ai/select \
     -H 'Content-Type: application/json' -d '{"name":"skops-local"}' -b cookies.txt
   ```
3. Anomali görürsen tek komut rollback:
   ```bash
   curl -s -X POST http://localhost:8000/ai/select \
     -H 'Content-Type: application/json' -d '{"name":"stub-sine"}' -b cookies.txt
   ```

---

## 🧪 Validasyon

### Hızlı Nabız

```bash
make health-check
```

### Tam Validasyon

```bash
make prod-ready
```

### SLA (tek çağrı ölçüm)

```bash
time curl -s 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s' >/dev/null
# Hedef: p95 < 200ms
```

---

## 📊 Monitoring (Prometheus)

**Metrikler**

- `levibot_model_latency_seconds` (summary)
- `levibot_predict_requests_total`
- `levibot_fallback_events_total`
- `levibot_features_staleness_seconds`
- `levibot_market_ticks_per_minute`
- `levibot_active_model_info`
- `levibot_model_switches_total`
- `levibot_errors_total`

**Alarm Önerileri**

- **DataStale60s:** staleness > 60s (3 dk)
- **LatencyP95High:** p95 > 300ms (5 dk)
- **PredictErrorSpike:** error rate > %1 (5 dk)
- **TicksDrop:** ticks/min < 30 (3 dk)

**Spot-check**

```bash
curl -s http://localhost:8000/metrics/prom | \
  grep -E 'latency|fallback|staleness|ticks|predict'
```

---

## 🔐 Güvenlik

**Login (cookie)**

```bash
curl -s -X POST http://localhost:8000/auth/admin/login \
  -H 'Content-Type: application/json' -d '{"key":"'"$ADMIN_KEY"'"}' -c cookies.txt
```

**Korumalı çağrı (ör.)**

```bash
curl -s -X POST http://localhost:8000/admin/unkill -b cookies.txt | jq
```

**IP Allowlist**: IP dışından gelen çağrılar 403.

**Audit Log**

```bash
tail -f ops/audit.log
```

---

## 🧯 Incident Runbook

- **Data stale** → sistem **silent fallback** yapar (UI çalışır).
- **Model sorunlu** → rollback:
  ```bash
  curl -s -X POST http://localhost:8000/ai/select \
    -H 'Content-Type: application/json' -d '{"name":"stub-sine"}' -b cookies.txt
  ```
- **Acil durdur**:
  ```bash
  curl -s -X POST http://localhost:8000/admin/kill -b cookies.txt | jq
  ```

---

## 🧰 Günlük Operasyon Komutları (Makefile)

```bash
make prod-ready       # full deployment check
make health-check     # cron için kısa sağlık kontrolü
make seed-data        # 10k demo tick
make ca-setup         # m1s/m5s continuous aggs
make train-prod       # prod modeli eğit
make backend-restart  # backend'i yeniden başlat
make model-test       # predict testi (fallback flag'li)
make snapshot-flags   # config snapshot
```

---

## 🗓️ Cron Önerisi (Health)

`/usr/local/bin/levibot-health.sh`:

```bash
#!/usr/bin/env bash
set -e
make health-check
```

Crontab:

```
*/5 * * * * /usr/local/bin/levibot-health.sh >> /var/log/levibot-health.log 2>&1
```

---

## ✅ Kabul Kriterleri (Go/No-Go)

- [ ] **Security:** Admin login, IP allowlist, audit çalışıyor
- [ ] **Predict:** p95 < 200ms, error < %0.1
- [ ] **Fallback:** DB kapalıyken fallback:true ve sistem ayakta
- [ ] **Deciles:** 10 bucket + CSV export
- [ ] **Monitoring:** metrikler geliyor, alarmlar yüklü
- [ ] **Docs:** bu playbook repo'da versiyonlandı ✔

---



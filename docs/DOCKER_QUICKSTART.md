# 🐳 Docker Quick Start - Tek Komutla Tüm Servisler

## 🚀 Başlatma (Tek Komut)

```bash
docker compose up -d
```

**Açılan Servisler:**

- ✅ API (Backend): http://localhost:8000
- ✅ Panel (Frontend): http://localhost:3002
- ✅ TimescaleDB: localhost:5432
- ✅ Redis: localhost:6379

---

## 📊 Servis Durumu Kontrolü

```bash
docker compose ps
```

---

## 🛑 Durdurma

```bash
# Tüm servisleri durdur
docker compose stop

# Tüm servisleri durdur ve kaldır
docker compose down
```

---

## 🔄 Yeniden Başlatma

```bash
# Tek servisi restart
docker compose restart api
docker compose restart panel

# Tümünü restart
docker compose restart
```

---

## 📝 Logları Görme

```bash
# Tüm loglar
docker compose logs -f

# Sadece API
docker compose logs -f api

# Sadece Panel
docker compose logs -f panel

# Son 50 satır
docker compose logs --tail 50 api
```

---

## 🔨 Rebuild (Kod Değiştikten Sonra)

### Panel Değişikliği

```bash
# Panel'i rebuild et
docker compose build panel

# Restart et
docker compose up -d panel
```

### API Değişikliği

```bash
# API'yi rebuild et
docker compose build api

# Restart et
docker compose up -d api
```

### Tümünü Rebuild

```bash
docker compose build --no-cache
docker compose up -d
```

---

## 🎯 Hızlı Testler

### API Test

```bash
curl -s http://localhost:8000/healthz | jq
curl -s http://localhost:8000/risk/guardrails | jq
```

### Panel Test

```bash
# Tarayıcıda
open http://localhost:3002/risk

# Terminal'de
curl -s http://localhost:3002/ | grep -o "<title>.*</title>"
```

### Model Test

```bash
curl -s 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s' | jq '{model, fallback, prob_up}'
```

---

## 🔧 Troubleshooting

### Port Çakışması

```bash
# Port'ları kontrol et
lsof -i :8000
lsof -i :3002
lsof -i :5432

# Çakışan process'i durdur
kill <PID>
```

### Container Sağlıksız

```bash
# Health status kontrol
docker compose ps

# Container'ı restart
docker compose restart <service_name>

# Logs kontrol
docker compose logs <service_name>
```

### Veri Tazeleme (Manuel)

```bash
# Container içinde
docker compose exec timescaledb psql -U postgres -d levibot -c "SELECT NOW();"

# Script ile
./scripts/keep_data_fresh.sh
```

---

## 📍 Servis Portları

| Servis      | Port | URL                   |
| ----------- | ---- | --------------------- |
| Panel       | 3002 | http://localhost:3002 |
| API         | 8000 | http://localhost:8000 |
| TimescaleDB | 5432 | localhost:5432        |
| Redis       | 6379 | localhost:6379        |

---

## ✅ Production Ready

### İlk Başlatma

```bash
# 1. Environment variables set et (.env.docker)
# 2. Tüm servisleri başlat
docker compose up -d

# 3. Health check
docker compose ps

# 4. Guardrails test
curl -s http://localhost:8000/risk/guardrails | jq

# 5. Panel'i aç
open http://localhost:3002/risk
```

### Monitoring

```bash
# Stats
docker stats

# Health
docker compose ps

# Logs (son 1 saat)
docker compose logs --since 1h
```

---

## 🎉 Özet

**Tek komutla her şey çalışır:**

```bash
docker compose up -d
```

**Guardrails kartını görmek için:**

```
http://localhost:3002/risk
```

**Durdurma:**

```bash
docker compose down
```

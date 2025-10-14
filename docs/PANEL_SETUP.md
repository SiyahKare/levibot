# 🎯 Panel Setup - Final Configuration

## 📍 Aktif Panel

**Dev Server (Güncel - Guardrails var):**

- URL: http://localhost:3002/
- Risk Sayfası: http://localhost:3002/risk
- Hot-reload: Aktif
- PID: Check with `ps aux | grep vite`

**Docker Panel (Eski - Kapatıldı):**

- Port 3001 kapatıldı çünkü eski kod (guardrails yok)

---

## 🛡️ Guardrails Sayfası

### Erişim

1. Tarayıcıda: http://localhost:3002/
2. Sol menüden "Risk" linkine tıkla
3. Aşağı scroll → "🛡️ Trade Guardrails" kartını gör

### Özellikler

- ✅ Confidence Threshold slider (0.50-1.00)
- ✅ Max Trade Size slider ($100-$2000)
- ✅ Max Daily Loss slider (-$500-$0)
- ✅ Cooldown Period slider (5-120 min)
- ✅ Circuit Breaker toggle
- ✅ Latency Threshold slider (100-1000ms)
- ✅ Symbol Allowlist (BTCUSDT/ETHUSDT/SOLUSDT/BNBUSDT)
- ✅ Save/Trigger Cooldown/Clear Cooldown butonları
- ✅ Real-time cooldown countdown badge

---

## 🔧 Troubleshooting

### "Risk sayfası çalışmıyor"

1. Tarayıcıda F12 → Console tab → Hata var mı?
2. Network tab → XHR/Fetch → API çağrıları başarılı mı?
3. http://localhost:8000/risk/guardrails → 200 dönüyor mu?

### Dev Server Restart

```bash
# Mevcut process'i bul ve durdur
ps aux | grep vite
kill <PID>

# Yeniden başlat
cd frontend/panel
npm run dev -- --port 3002 --host 0.0.0.0
```

### API Test

```bash
# Guardrails endpoint
curl -s http://localhost:8000/risk/guardrails | jq

# Model status
curl -s 'http://localhost:8000/ai/predict?symbol=BTCUSDT&h=60s' | jq
```

---

## 📊 Sistem Durumu Kontrol

```bash
# Hızlı check
./scripts/canary_check.sh

# Dev server çalışıyor mu?
lsof -i :3002

# API çalışıyor mu?
curl -s http://localhost:8000/healthz

# Auto-refresh çalışıyor mu?
ps aux | grep auto_refresh
```

---

## 🚀 Production Build (İleride)

Docker panel'i yeniden aktif etmek için:

```bash
# Panel'i rebuild et (yeni kod ile)
docker compose build panel

# Başlat
docker compose up -d panel

# Test
open http://localhost:3001/risk
```

---

## ✅ Current Status

- Dev Panel: ✅ Running (3002)
- Docker Panel: ❌ Stopped (conflict çözüldü)
- API: ✅ Running (8000)
- Guardrails: ✅ Active
- Model: ✅ skops-local (fallback: false)
- Auto-refresh: ✅ Running

**Kullan:** http://localhost:3002/risk

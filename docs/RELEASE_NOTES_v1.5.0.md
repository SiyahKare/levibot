# 🚀 LeviBot v1.5.0 — Test Data Seeder + Events Fix

**Çıkış Tarihi:** 2025-10-06  
**Kod adı:** Sprint Hotfix — Data & Events

---

## 🎯 Öne Çıkanlar

### 🌱 Test Data Seeder
- **Comprehensive Test Data Generator** — 5 farklı event türü (SIGNAL_SCORED, POSITION_CLOSED, DEX_QUOTE, MEV_ARB_OPP, SIGNAL_INGEST)
- **Flexible Seeding** — today/week/minimal/cleanup komutları
- **Realistic Data** — gerçekçi timestamp, symbol, confidence, PnL değerleri
- **Easy Cleanup** — test dosyalarını takip edip temizleme

### 🔧 Events API Fix
- **Simplified `/events` endpoint** — karmaşık filter mantığı kaldırıldı
- **Working Data Flow** — 9296 satır okunup 0 event dönen bug çözüldü
- **Recent-First Sorting** — en yeni event'ler önce gösteriliyor
- **Multi-Source Support** — hem klasör hem root-level JSONL dosyaları

### 🐳 Production Docker (devam)
- **Fixed Build Issues** — C extension compilation için gcc/g++/make eklendi
- **Volume Mounting** — log ve ml verilerinin persistence'ı
- **Port Conflict Resolution** — Panel 3001'e taşındı

---

## 📦 İçerik / Değişiklikler

**Backend:**
- `backend/src/testing/seed_data.py` — kapsamlı test data seeder
- `backend/src/app/reports.py` — basitleştirilmiş `/events` endpoint
- `Dockerfile.api` — C extension build desteği (gcc, g++, make, python3-dev)
- `backend/requirements.txt` — pandas==2.2.3 eklendi

**Ops:**
- `docker-compose.yml` — panel portu 3000→3001
- `.env.docker` — LOG_DIR ve diğer Docker-specific ayarlar

**Documentation:**
- Test data seeding kullanımı
- Events API debugging notları

---

## 🔧 Hızlı Başlangıç (Docker)

```bash
git clone https://github.com/SiyahKare/levibot.git
cd levibot
cp .env.docker.example .env
# .env içinde API_KEYS ve LOG_DIR=/app/backend/data/logs ayarla
make docker-up

# Test datası oluştur
docker exec levibot-api python3 -m backend.src.testing.seed_data today   # Bugün (55 events)
docker exec levibot-api python3 -m backend.src.testing.seed_data week    # 7 gün (385 events)

# Panel: http://localhost:3001  |  API: http://localhost:8000
```

**Smoke Test:**

```bash
# Health
curl -s http://localhost:8000/healthz | jq

# Events (artık çalışıyor!)
curl -s 'http://localhost:8000/events?days=1&limit=10' | jq

# Seeder test
docker exec levibot-api python3 -m backend.src.testing.seed_data minimal
curl -s 'http://localhost:8000/events?limit=5' | jq '. | length'
docker exec levibot-api python3 -m backend.src.testing.seed_data cleanup
```

---

## 🐛 Düzeltilen Buglar

### Events API Boş Dönüyordu (Kritik)
**Problem:**
- `/events` endpoint 9296 satır okuyordu ama 0 event döndürüyordu
- Karmaşık filter mantığı (trace_id, event_type, symbol, q, since) tüm event'leri eliyordu
- Nested loop kontrollerinde `break` yanlış seviyede çalışıyordu

**Çözüm:**
- Filter mantığını tamamen kaldırdık
- Basit dosya okuma + timestamp sort mantığı
- `limit` kontrolü düzgün seviyede (`break` hem inner hem outer loop için)
- En yeni event'ler önce (reverse sort)

**Sonuç:** ✅ 10/10 events başarıyla döndürülüyor

### Docker Build Hataları
**Problem:**
- `lru-dict` wheel build ederken `gcc` bulunamıyordu
- Port 3000 çakışması (başka bir servis kullanıyordu)

**Çözüm:**
- `gcc`, `g++`, `make`, `python3-dev` eklendi
- Panel portu 3001'e taşındı
- `pandas` dependency eksikliği giderildi

---

## 📊 İstatistikler

* **Yeni Modüller:** 1 (seed_data.py)
* **Düzeltilen Endpoint:** 1 (/events)
* **Test Events:** 55 (today), 385 (week)
* **Event Türleri:** 5 (SIGNAL_SCORED, POSITION_CLOSED, DEX_QUOTE, MEV_ARB_OPP, SIGNAL_INGEST)
* **Docker Build Time:** ~5 dakika (ilk build), ~30 saniye (incremental)

---

## 🛠️ Test Data Seeder Kullanımı

```bash
# Bugün için tam set (55 events)
docker exec levibot-api python3 -m backend.src.testing.seed_data today

# 7 gün için tam set (385 events)
docker exec levibot-api python3 -m backend.src.testing.seed_data week

# Minimal set (5 events) - hızlı test için
docker exec levibot-api python3 -m backend.src.testing.seed_data minimal

# Temizlik - oluşturulan test dosyalarını sil
docker exec levibot-api python3 -m backend.src.testing.seed_data cleanup

# Tehlikeli - TÜM log dosyalarını sil (production'da kullanma!)
docker exec levibot-api python3 -m backend.src.testing.seed_data cleanup-all
```

**Event Türleri:**
- `SIGNAL_SCORED` — ML model confidence skoru
- `AUTO_ROUTE_EXECUTED` — Otomatik trade başlatma
- `POSITION_CLOSED` — Trade kapatma (PnL ile)
- `DEX_QUOTE` — DEX fiyat teklifi
- `MEV_ARB_OPP` — MEV arbitraj fırsatı
- `SIGNAL_INGEST` — Telegram sinyal alımı

---

## ⚠️ Breaking Changes

Yok — tamamen geriye uyumlu.

---

## 🔜 Sonraki Adımlar (v1.6.0)

- [ ] Events API'ye filter parametreleri geri ekle (optional, test edilmiş)
- [ ] Seeder'a custom event türü desteği
- [ ] Panel'de event timeline görselleştirmesi
- [ ] Real-time event streaming (WebSocket)
- [ ] Event replay/debug modu

---

## 🙏 Teşekkürler

Bu sürüm, production'da karşılaşılan kritik bir bug'ı (boş events API) çözmek ve test ortamını iyileştirmek için acil olarak hazırlandı.

**Keyifli kullanımlar! 🚀**


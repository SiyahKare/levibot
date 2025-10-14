# 🚀 LeviBot Enterprise — AI-Powered Signals Platform

<p align="center">
  <strong>Enterprise-grade AI Signals Platform with 24/7 Data Collection, ML/AI Decision Engine, Telegram Bot & Mini App</strong>
</p>

<p align="center">
  <a href="https://github.com/siyahkare/levibot/releases">
    <img src="https://img.shields.io/github/v/tag/SiyahKare/levibot?label=release" alt="Release">
  </a>
  <a href="https://github.com/siyahkare/levibot/actions/workflows/ci.yml">
    <img src="https://github.com/siyahkare/levibot/actions/workflows/ci.yml/badge.svg" alt="CI Status">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
  </a>
  <a href="https://fastapi.tiangolo.com/">
    <img src="https://img.shields.io/badge/FastAPI-0.114+-green.svg" alt="FastAPI">
  </a>
  <a href="https://react.dev/">
    <img src="https://img.shields.io/badge/React-18+-blue.svg" alt="React">
  </a>
</p>

---

## ⚡ Hızlı Başlangıç (5 Dakika)

```bash
# 1. Environment dosyasını kopyala ve düzenle
cp ENV.levibot.example .env
nano .env  # TG_BOT_TOKEN, BINANCE_KEY, vb. ekle

# 2. Sistemi başlat (Docker gerekli)
make up

# 3. Durum kontrolü
make ps

# 4. Smoke test çalıştır
make smoke-test

# 5. Telegram bot'una /start gönder
# Mini App panelini aç ve canlı PnL'i izle!
```

**Detaylı kurulum için:** [docs/QUICKSTART.md](./docs/QUICKSTART.md)

---

## 🎯 Özellikler

### 🤖 AI/ML Signals Engine

- **LightGBM** tabanlı ML pipeline
- Real-time feature engineering (z-score, VWAP, ATR, OFI)
- Multi-strategy orchestration (ML + Rule-based)
- Confidence scoring & policy filtering

### 📊 Event-Driven Architecture

- **Redis Streams** event bus
- Asynchronous signal → decision → execution flow
- Circuit breakers & retry logic
- Hot feature cache

### 💾 Enterprise Storage

- **ClickHouse** for time-series data
- **Redis** for hot state & queues
- **DuckDB/Parquet** for research
- Automated backups & TTL policies

### 📱 Telegram Integration

- **Telegram Bot** for commands & alerts
- **Mini App (WebApp)** for live dashboard
- Real-time PnL, equity curve, signal history
- Kill-switch & trading controls

### 📈 Observability

- **Prometheus** metrics collection
- **Grafana** dashboards (PnL, latency, hit-rate)
- Audit logging to ClickHouse
- Health checks & alerting

### 🔒 Production-Ready

- HMAC authentication for Mini App
- Role-based access control
- Rate limiting & exponential backoff
- Config checksums & canary deployments

---

## 📦 Mimari

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot + Mini App                  │
│              (Commands, Alerts, Live Dashboard)             │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                      Panel API (FastAPI)                    │
│         /policy/status, /signals/recent, /analytics         │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼────────┐ ┌───▼────────┐ ┌───▼──────────┐
│ Signal Engine   │ │  Executor  │ │ Feature      │
│ (ML + Rules)    │ │  (Orders)  │ │ Builder      │
└────────┬────────┘ └───┬────────┘ └───┬──────────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │   Redis Streams (Event Bus) │
         │  signals.*, orders.*, etc.  │
         └──────────────┬──────────────┘
                        │
         ┌──────────────┼──────────────┐
         │              │              │
┌────────▼────────┐ ┌──▼───────────┐ ┌▼──────────────┐
│  ClickHouse     │ │    Redis     │ │  Prometheus   │
│  (Time-Series)  │ │  (Hot Cache) │ │   (Metrics)   │
└─────────────────┘ └──────────────┘ └───────────────┘
```

---

## 🛠️ Teknoloji Stack

**Backend:**

- Python 3.11+, FastAPI, Uvicorn
- LightGBM, NumPy, Pandas
- CCXT (exchange integration)
- Redis (aioredis), ClickHouse
- Prometheus client

**Frontend:**

- React 18, TypeScript
- Telegram WebApp SDK
- Recharts, SWR, TailwindCSS

**Infrastructure:**

- Docker & Docker Compose
- Prometheus & Grafana
- GitHub Actions (CI/CD)

---

## 📚 Dokümantasyon

### Kullanıcı Dokümanları

- **[docs/QUICKSTART.md](./docs/QUICKSTART.md)** - 5 dakikada başla
- **[docs/DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md)** - Detaylı deployment
- **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** - Sistem mimarisi
- **[docs/ML_SPRINT3_GUIDE.md](./docs/ML_SPRINT3_GUIDE.md)** - ML pipeline
- **[docs/RUNBOOK_PROD.md](./docs/RUNBOOK_PROD.md)** - Production runbook
- **[docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md)** - Katkıda bulunma kılavuzu
- **[docs/SECURITY.md](./docs/SECURITY.md)** - Güvenlik politikası

### Planlama & Yol Haritası 🗺️

- **[docs/PLANNING_INDEX.md](./docs/PLANNING_INDEX.md)** - 📚 Planlama dokümanları index
- **[docs/ROADMAP.md](./docs/ROADMAP.md)** - 🗺️ Public roadmap (GitHub-friendly)
- **[docs/DEVELOPMENT_PLAN_SUMMARY.md](./docs/DEVELOPMENT_PLAN_SUMMARY.md)** - 📊 Yönetici özeti (5 dk)
- **[docs/DEVELOPMENT_ROADMAP.md](./docs/DEVELOPMENT_ROADMAP.md)** - 📋 12 aylık detaylı plan (30 dk)
- **[docs/SPRINT_PLANNING.md](./docs/SPRINT_PLANNING.md)** - ⚙️ Sprint execution guide (15 dk)
- **[docs/TECHNICAL_EVOLUTION.md](./docs/TECHNICAL_EVOLUTION.md)** - 🔧 Teknik mimari evrim planı (20 dk)

### Aktif Sprint 🏃

**✅ Sprint-9: "Gemma Fusion"** → **TAMAMLANDI!**  
_Multi-engine stabilization, AI Fusion, Risk Manager v2, CI/CD Pipeline, Nightly AutoML_

**🔥 Sprint-10: "The Real Deal"** (15-31 Ekim 2025)  
_Production models + Real data: ccxt/MEXC, LGBM/TFT training, Backtesting, Testnet live prep_

- **[sprint/S10_THE_REAL_DEAL_PLAN.md](./sprint/S10_THE_REAL_DEAL_PLAN.md)** - 🚀 Sprint-10 Master Plan
- **[sprint/S10_TASKS.yaml](./sprint/S10_TASKS.yaml)** - 📋 Sprint-10 Task Tracker
- **[sprint/SPRINT9_COMPLETION_FINAL.md](./sprint/SPRINT9_COMPLETION_FINAL.md)** - 🎊 Sprint-9 Complete (100%)

**Sprint-10 Progress: 4/5 Epics Complete** 🚀

**Epic-A: Real Data Ingestion (COMPLETE ✅)**

- **[sprint/EPIC_A_CCXT_GUIDE.md](./sprint/EPIC_A_CCXT_GUIDE.md)** - 📘 Implementation Guide
- **[sprint/EPIC_A_CCXT_COMPLETE.md](./sprint/EPIC_A_CCXT_COMPLETE.md)** - ✅ Completion Summary
- Mock Soak: **PASS** (0% drop, 0 errors, Q95=0.3)

**Data Flow:**

```
MEXC (ccxt.pro WS) → MarketFeeder (gap-fill) → Symbol-specific Engine Queue → Ensemble/Risk
```

**Epic-B: Production LGBM (COMPLETE ✅)**

- **[sprint/EPIC_B_LGBM_GUIDE.md](./sprint/EPIC_B_LGBM_GUIDE.md)** - 📘 Implementation Guide
- **[sprint/EPIC_B_LGBM_COMPLETE.md](./sprint/EPIC_B_LGBM_COMPLETE.md)** - ✅ Completion Summary
- Model: `backend/data/models/best_lgbm.pkl` (Optuna-tuned, 32 trials)
- Model Card: `backend/data/models/2025-10-14/model_card_lgbm.json`
- Inference: `LGBMProd.predict_proba_up(features)` (thread-safe)

**Epic-C: Production TFT (COMPLETE ✅)**

- **[sprint/EPIC_C_TFT_COMPLETE.md](./sprint/EPIC_C_TFT_COMPLETE.md)** - ✅ Completion Summary
- Model: `backend/data/models/best_tft.pt` (PyTorch Lightning, LSTM backbone)
- Model Card: `backend/data/models/2025-10-14/model_card_tft.json`
- Architecture: `TinyTFT` (lookback=60, horizon=5, val_acc=50.8%)
- Inference: `TFTProd.predict_proba_up(seq_window)` (thread-safe singleton)

**Epic-D: Backtesting Framework (COMPLETE ✅)**

- **[sprint/EPIC_D_BACKTEST_GUIDE.md](./sprint/EPIC_D_BACKTEST_GUIDE.md)** - 📘 Implementation Guide
- **[sprint/EPIC_D_BACKTEST_COMPLETE.md](./sprint/EPIC_D_BACKTEST_COMPLETE.md)** - ✅ Completion Summary
- Vectorized runner: t+1 mid-price fills + transaction costs (fee+slippage in bps)
- Metrics: Sharpe, Sortino, Max Drawdown, Hit Rate, Turnover
- Reports: Markdown + JSON + NPY artifacts (`reports/backtests/`)
- Tests: 2/2 smoke tests passing ✅

**Epic-1: Multi-Engine (Sprint-9 ✅)**

- **[sprint/EPIC1_ENGINE_MANAGER_GUIDE.md](./sprint/EPIC1_ENGINE_MANAGER_GUIDE.md)** - 🔥 Implementation Guide
- **[sprint/EPIC1_QUICKSTART.md](./sprint/EPIC1_QUICKSTART.md)** - ⚡ Quick Start
- **[sprint/EPIC1_COMPLETION_SUMMARY.md](./sprint/EPIC1_COMPLETION_SUMMARY.md)** - 📊 Summary

**Epic-2: AI Fusion (COMPLETE ✅)**

- **[sprint/EPIC2_AI_FUSION_COMPLETE.md](./sprint/EPIC2_AI_FUSION_COMPLETE.md)** - 🧠 AI Fusion Summary

**Epic-3: Risk Manager (COMPLETE ✅)**

- **[sprint/EPIC3_RISK_MANAGER_COMPLETE.md](./sprint/EPIC3_RISK_MANAGER_COMPLETE.md)** - 🛡️ Risk Management Summary

**Monitoring & Observability (COMPLETE ✅)**

- **[sprint/MONITORING_QUICKSTART.md](./sprint/MONITORING_QUICKSTART.md)** - 📊 Prometheus + Grafana + Soak Test
- **[sprint/SOAK_TEST_RESULTS.md](./sprint/SOAK_TEST_RESULTS.md)** - 🧪 Soak Test Results & System Validation

**Epic-4: CI/CD Pipeline (COMPLETE ✅)**

- **[sprint/EPIC4_CICD_COMPLETE.md](./sprint/EPIC4_CICD_COMPLETE.md)** - 🚀 CI/CD Pipeline & GitHub Actions

**Epic-5: Nightly AutoML (COMPLETE ✅)**

- **[sprint/EPIC5_AUTOML_COMPLETE.md](./sprint/EPIC5_AUTOML_COMPLETE.md)** - 🌙 Nightly AutoML Pipeline

---

## 🔧 Makefile Komutları

```bash
# Geliştirme
make init          # Geliştirme ortamını kur
make lint          # Kod kalitesini kontrol et
make format        # Kodu otomatik formatla
make test          # Testleri çalıştır
make cov           # Test coverage raporu

# Docker
make docker        # Docker image'ını build et
make up            # Tüm servisleri başlat
make down          # Tüm servisleri durdur
make logs          # Tüm logları izle
make smoke         # Smoke test (health check)

# Utilities
make automl        # Manuel AutoML pipeline çalıştır
make clean         # Cache ve geçici dosyaları temizle
```

---

## 🔄 CI/CD Pipeline

LeviBot, GitHub Actions ile tam otomatik CI/CD pipeline'ına sahiptir:

### Pipeline Stages

```
📝 Lint  →  🧪 Test  →  📊 Coverage  →  🐳 Docker  →  🔒 Security  →  🚀 Deploy
```

**PR'larda:**

- ✅ Ruff + Black + isort (kod kalitesi)
- ✅ Pytest (42 passing tests)
- ✅ Coverage ≥75% threshold
- ✅ Docker image build
- ✅ Trivy security scan

**Main branch'te:**

- ✅ Tüm yukarıdakiler +
- ✅ GHCR'ye image push
- ✅ Deploy aşaması (yapılandırılabilir)

### Docker Image

```bash
# Pull latest image
docker pull ghcr.io/siyahkare/levibot:latest

# Run locally
docker run -p 8000:8000 ghcr.io/siyahkare/levibot:latest
```

### Pre-commit Hooks

```bash
# Setup
make init  # pre-commit hooks otomatik kurulur

# Manuel çalıştır
pre-commit run --all-files
```

---

## 🎮 Kullanım Örnekleri

### Telegram Bot Komutları

```
/start       - Bot'u başlat ve Mini App'i aç
/status      - Sistem durumunu göster
/killswitch  - Acil durdurma (toggle)
```

### Mini App Özellikleri

- 📊 **Live Equity Curve** (son 24 saat)
- 💰 **Real-time PnL** (günlük, toplam)
- 🎯 **Recent Signals** (son 10 sinyal)
- 🔴 **Kill Switch** (tek tıkla durdur)
- ⚙️ **Trading Toggle** (aç/kapat)

### API Endpoints

```bash
# Sistem durumu
curl http://localhost:8080/policy/status

# Son sinyaller
curl http://localhost:8080/signals/recent?limit=10

# Equity curve
curl http://localhost:8080/analytics/equity?hours=24

# Günlük istatistikler sıfırla
curl -X POST http://localhost:8080/policy/reset_daily
```

---

## 🐛 Sorun Giderme

**Servis ayağa kalkmıyor:**

```bash
make logs-[service_name]  # Logları kontrol et
docker compose -f docker-compose.enterprise.yml restart [service_name]
```

**Telegram bot yanıt vermiyor:**

```bash
make logs-bot
# .env dosyasında TG_BOT_TOKEN'ı kontrol et
```

**ClickHouse bağlantı hatası:**

```bash
make init-db  # Veritabanını yeniden başlat
```

Daha fazla bilgi için: [QUICKSTART.md](./QUICKSTART.md)

---

## 📊 Monitoring & Dashboards

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Panel API:** http://localhost:8080
- **Mini App:** http://localhost:5173

---

## 🤝 Katkıda Bulunma

1. Fork'la
2. Feature branch oluştur (`git checkout -b feature/amazing`)
3. Commit'le (`git commit -m 'Add amazing feature'`)
4. Push'la (`git push origin feature/amazing`)
5. Pull Request aç

---

## 📄 Lisans

MIT License - Detaylar için [LICENSE](./LICENSE) dosyasına bakın.

---

## 🙏 Teşekkürler

Bu proje aşağıdaki harika açık kaynak projelerden yararlanmaktadır:

- [FastAPI](https://fastapi.tiangolo.com/)
- [LightGBM](https://lightgbm.readthedocs.io/)
- [CCXT](https://github.com/ccxt/ccxt)
- [ClickHouse](https://clickhouse.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

<p align="center">
  <strong>🚀 LeviBot Enterprise - AI-Powered Trading Signals Platform</strong><br>
  Made with ❤️ by the LeviBot Team
</p>
>
> ### 📊 Smart Event Filters (v1.6.0+)
> ```bash
> # Filter by event type (CSV list)
> curl 'http://localhost:8000/events?event_type=SIGNAL_SCORED,POSITION_CLOSED&limit=10'
> 
> # Filter by symbol
> curl 'http://localhost:8000/events?symbol=BTCUSDT&limit=10'
> 
> # Full-text search in payload
> curl 'http://localhost:8000/events?q=confidence&limit=10'
> 
> # Date range filter
> curl 'http://localhost:8000/events?since_iso=2025-10-06T00:00:00Z&limit=10'
> 
> # Combined filters
> curl 'http://localhost:8000/events?event_type=SIGNAL_SCORED&symbol=ETHUSDT&q=buy&limit=10'
> ```
>
> ### 🎯 Event Timeline UI (v1.6.0+)
> **Panel üzerinde interaktif zaman çizelgesi:**
> - **Recharts scatter plot** ile görselleştirme
> - **15+ event type** için renk kodlaması
> - **Quick filters**: 24h / 7d / 30d butonları
> - **Smart filters**: event type, symbol, text search
> - **Trace highlighting**: Event'e tıkla → aynı trace_id'li tüm event'ler vurgulanır
> - **Auto-refresh**: Her 10 saniyede otomatik yenilenir
> - **Recent events table**: Son 12 event'in JSON detayları
>
> 📍 **Panel'de "Event Timeline" kartını göreceksin!**
>
> ### ⚡ Real-time WebSocket Stream (v1.6.0+)
> **Canlı event akışı WebSocket ile:**
> ```bash
> # WebSocket endpoint (filtrelenebilir)
> wscat -c 'ws://localhost:8000/ws/events?event_type=SIGNAL_SCORED,POSITION_CLOSED'
> 
> # Panel'de:
> # - Connection status badge (connected/connecting/disconnected)
> # - Live toggle checkbox
> # - Real-time event updates (no refresh)
> # - Auto-reconnect with exponential backoff
> # - Fallback to 10s polling when disabled
> ```
>
> **Metrikler:**
> - `levibot_ws_conns`: Aktif WebSocket bağlantıları
> - `levibot_ws_msgs_out_total`: Gönderilen mesaj sayısı
> - `levibot_ws_msgs_drop_total`: Backpressure'dan düşen mesajlar
>
> ### 📊 Analytics Dashboard (v1.6.0+)
> **Event verilerini görsel insights'a dönüştürür:**
> ```bash
> # Backend API endpoints
> curl 'http://localhost:8000/analytics/stats?days=1'          # Event dağılımı + top symbols
> curl 'http://localhost:8000/analytics/timeseries?interval=5m' # Time-series (1m/5m/15m/1h)
> curl 'http://localhost:8000/analytics/traces?limit=20'       # Top active traces
> ```
>
> **Panel Dashboard:**
> - **Event Type Distribution**: Pie chart (event tipleri dağılımı)
> - **Events Timeline**: Line chart (zaman serisi, bucket'lı)
> - **Top Symbols**: Bar chart (en aktif 10 sembol)
> - **Top Traces**: Table (event sayısı + süre)
> - **Auto-refresh**: 30 saniyede bir
> - **Filters**: days (1/7/30), interval (1m/5m/15m/1h), event_type CSV
>
> ### ⚡ Manuel Dev Setup
> ```bash
> python3 -m venv .venv && source .venv/bin/activate
> pip install -r backend/requirements.txt
> cp .env.example .env || cp ENV.example .env
> ./.venv/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload
> # smoke test
> curl -s http://127.0.0.1:8000/status | jq
> ```

LeviBot; Telegram kaynaklı sinyalleri toplar, puanlar ve izler; on‑chain/MEV/NFT akışlarından üretilen uyarıları tek bir izleme/logging ve panel mimarisine düşürür. Risk‑first yaklaşımı ve çok kullanıcılı yapı için tasarlanmıştır.

## Özellikler (Checklist)

- [x] FastAPI backend (`/status`, `/start`, `/stop`, `/config`, `/events`)
- [x] JSONL logging + DuckDB raporlama (`backend/src/infra/logger.py`, `app/reports.py`)
- [x] Telegram ingest
  - [x] Bot API (aiogram) → `backend/src/ingest/telegram_signals.py`
  - [x] User‑bot (Telethon) auto‑discover + backfill → `telegram/user_client.py`
- [x] Sinyal parser (regex) → `telegram/signal_parser.py`
- [x] Panel (Vite+React+TS) → `frontend/panel`
- [x] Kullanıcı/rol konfigürasyonu → `backend/configs/users.yaml`
- [x] Risk guard ve exec iskeleti (Bybit/Binance stub’ları) → `backend/src/exec/*`
- [x] Raporlar: günlük/haftalık, Telegram reputation → `backend/src/app/reports.py`
- [x] Dark‑data modülleri (iskele)
  - [x] On‑chain Listener (WS) → `backend/src/onchain/listener.py`
  - [x] MEV DEX‑DEX arb scan → `backend/src/mev/arb_scan.py`
  - [x] NFT Sniper (Reservoir) → `backend/src/nft/sniper.py`
- [ ] Ödeme/VIP abonelik katmanı (yok)
- [ ] Canlı DEX quoter/pricer ve MEV‑Share entegrasyonu (yok)

## Klasör Yapısı (özet)

```
backend/
  configs/      # users, risk, symbols, features, model, telegram + onchain/mev/nft
  src/
    app/       # FastAPI, /events dahil
    infra/     # logger, duckdb yardımcıları
    ingest/    # Telegram Bot API ingest
    telegram/  # Telegram bot komutları (aiogram)
    exec/      # exchange router ve risk/oco iskeletleri
    features/, signals/, models/, news/, risk/, reports/
frontend/panel/ # React panel
telegram/       # Telethon user‑bot (auto‑discover + backfill + live)
```

## Mevcut Durum (Kısa Özet)

- **Logging**: Çalışır (JSONL saatlik shard). `/events` endpoint’i `event_type` filtresi ile hazır.
- **Sinyal alma**: Bot API ve Telethon user‑bot aktif. Regex parser mevcut.
- **Sinyal gönderme/notify**: `backend/src/alerts/notify.py` ile Telegram’a bildirim gönderimi var (ENV gerekli).
- **Yürütme (exec)**: Bybit/Binance için iskelet/stub router, TWAP vb. var; gerçek emir akışı için anahtarlar ve ayar gerekir.
- **Raporlama**: Günlük/haftalık özet ve Telegram reputation. Not: `telegram_eval.py` pandas’a ihtiyaç duyar.
- **Panel**: Çalışır mini panel; On‑Chain / MEV Feed / NFT Sniper sayfaları eklendi (iskele veri okur).
- **Ödeme/abonelik/VIP**: Bulunmadı (TODO). Kullanıcı rolleri var ama ödeme entegrasyonu yok.
- **On‑chain/MEV/NFT**: İskelet modüller mevcut; canlı fiyat/quote ve private tx için entegrasyon gereken yerler TODO.

## 🐳 Docker Setup

### **Architecture**

```
┌─────────────────────────────────────────┐
│  Panel (Nginx:80 → localhost:3000)     │
│  ├─ Static assets (/usr/share/nginx)   │
│  └─ API proxy (/api/* → api:8000)      │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  API (Uvicorn:8000)                     │
│  ├─ FastAPI backend                     │
│  ├─ Redis client (rate limiting)        │
│  └─ Volumes: logs, configs              │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│  Redis (6379)                           │
│  └─ Distributed rate limit + cache      │
└─────────────────────────────────────────┘
```

### **Services**

- 🚀 **API** — FastAPI backend (port 8000)
- 🎨 **Panel** — React dashboard (port 3000)
- 🗄️ **Redis** — Distributed rate limiting (port 6379)
- 🌐 **Nginx** — Reverse proxy + static serving

### **Commands**

```bash
# Build images
make docker-build

# Start all services (detached)
make docker-up

# View logs (follow mode)
make docker-logs

# List running services
make docker-ps

# Stop all services
make docker-down

# Restart services
make docker-restart

# Clean all containers/volumes/images
make docker-clean

# Shell into containers
make docker-shell-api    # API container
make docker-shell-redis  # Redis CLI
```

### **Health Checks**

```bash
# API health
curl http://localhost:8000/healthz

# Redis health
docker exec levibot-redis redis-cli ping

# All service statuses
make docker-ps
```

### **Production Deploy**

```bash
# 1. Build with version tag
BUILD_VERSION=1.5.0 BUILD_SHA=$(git rev-parse --short HEAD) make docker-build

# 2. Start stack
make docker-up

# 3. Monitor logs
make docker-logs

# 4. Verify build info
curl http://localhost:8000/metrics/prom | grep levibot_build_info
```

### **Environment Variables**

Core settings in `.env`:

- `API_KEYS` — Comma-separated API keys for authentication
- `REDIS_URL` — Redis connection string
- `CORS_ORIGINS` — Allowed CORS origins
- `SLACK_WEBHOOK_URL` / `DISCORD_WEBHOOK_URL` — Alert webhooks
- `RISK_POLICY` — Risk management policy (conservative/moderate/aggressive)
- `AUTO_ROUTE_ENABLED` — Enable auto-routing for signals
- `ALERT_AUTO_TRIGGER_ENABLED` — Enable auto-alerts for high-confidence signals

See `.env.docker.example` for full configuration.

---

## E2E Tests (Local)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
make e2e   # httpx + live uvicorn
# → 3 passed in ~9s
```

## S3 Log Archiver (Ops)

```bash
# Dry-run
make archive-dry
# Docker job
docker compose -f ops/docker-compose-cron.yml run --rm archive
```

## MinIO Local (S3-compatible)

```bash
# Start MinIO stack
make minio-up
# Console: http://localhost:9001 (user/pass: minioadmin/minioadmin)

# Test archiver with MinIO (real upload)
make archive-minio

# Stop MinIO
make minio-down
```

### Alerts — Webhook Queue (PR-35) & Slack/Discord (PR-36)

Async, rate-limited, retry'li webhook gönderim kuyruğu + zengin formatlı Slack/Discord entegrasyonu.

**ENV:**

- `ALERTS_OUTBOUND_ENABLED`: Webhook queue'yu etkinleştir (default: true)
- `WEBHOOK_RATE_LIMIT`: Hedef başına rate limit (req/sec, default: 1)
- `WEBHOOK_RETRY_MAX`: Maksimum retry sayısı (default: 3)
- `WEBHOOK_TIMEOUT`: HTTP timeout (saniye, default: 5)
- `WEBHOOK_BACKOFF_BASE`, `WEBHOOK_BACKOFF_MAX`, `WEBHOOK_JITTER`: Retry backoff ayarları
- `SLACK_WEBHOOK_URL`: Slack incoming webhook URL (opsiyonel)
- `DISCORD_WEBHOOK_URL`: Discord webhook URL (opsiyonel)
- `ALERT_DEFAULT_TARGETS`: Virgülle ayrılmış hedefler (opsiyonel, örn: "slack,discord")

**Metrikler:**

- `levibot_alerts_enqueued_total`: Kuyruğa eklenen alert sayısı
- `levibot_alerts_sent_total`: Başarıyla gönderilen alert sayısı
- `levibot_alerts_failed_total`: Tüm retry'lardan sonra başarısız olan alert sayısı
- `levibot_alerts_retry_total`: Retry sayısı
- `levibot_alerts_queue_size`: Mevcut kuyruk boyutu

**Kullanım (programatik):**

```python
from backend.src.app.main import WEBHOOK_QUEUE
from backend.src.alerts.channels import deliver_alert_via, route_targets

alert = {
    "title": "High-Confidence BUY",
    "summary": "BTC/USDT signal @60000 (conf 0.84)",
    "severity": "high",  # info | low | medium | high | critical
    "source": "signals",
    "labels": {"symbol": "BTC/USDT", "side": "buy", "conf": "0.84"},
    "url": "http://localhost:8000/signals"
}

# Auto-route to all configured channels
for target in route_targets():
    deliver_alert_via(target, alert, WEBHOOK_QUEUE)
```

**Format Örnekleri:**

- **Slack**: Blocks API (başlık, özet, alanlar, context footer, buton)
- **Discord**: Embeds (renk-kodlu severity, timestamp, alanlar, footer)
- **Severity Renkleri**: info=mavi, high=turuncu, critical=kırmızı

### Alerts — API & Auto-Trigger (PR-37)

Alert sistemi artık API endpoint'leri ve otomatik tetikleme ile canlı!

**API Endpoints:**

**POST /alerts/trigger** — Manuel alert tetikleme (test/demo için)

```bash
curl -X POST http://localhost:8000/alerts/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "title": "High-Confidence BUY",
    "summary": "BTC/USDT signal @60000 (conf 0.84)",
    "severity": "high",
    "source": "manual",
    "labels": {"symbol": "BTC/USDT", "side": "buy"}
  }'

# Response: {"status": "queued", "targets": ["slack", "discord"]}
```

**GET /alerts/history** — Alert geçmişi

```bash
curl "http://localhost:8000/alerts/history?limit=50&severity=high&days=7"

# Response: {"alerts": [...], "total": 42}
```

**Auto-Trigger:**

- Yüksek güven skorlu sinyaller otomatik olarak alert tetikler
- `/signals/ingest-and-score` içinde rule engine ile değerlendirme
- ENV ile eşik ve hedef konfigürasyonu

**ENV:**

- `ALERT_AUTO_TRIGGER_ENABLED`: Otomatik tetikleme (default: true)
- `ALERT_MIN_CONF`: Minimum güven skoru eşiği (default: 0.8)
- `ALERT_LOG_DIR`: Alert log dizini (default: backend/data/alerts)

**Metrikler:**

- `levibot_alerts_triggered_total{source="auto|manual"}`: Tetiklenen alert sayısı

**Örnek Flow:**

1. Telegram'dan signal gelir → `/signals/ingest-and-score`
2. ML model skorlar → confidence 0.85
3. Rule engine değerlendirir → `high_conf_buy` rule match
4. Auto-trigger çalışır → Slack/Discord'a gönderir
5. JSONL'e loglanır → Panel'de görünür (PR-38)

### Alerts — Panel Monitor (PR-38)

Frontend alert monitoring dashboard — **Sprint 8-A COMPLETE!** 🎊

**Özellikler:**

- 📊 **Live Alert Table**: timestamp, title, severity (color-coded), source, details
- 🔴 **Unread Badge**: Shows new alerts since last view
- 🔍 **Filters**: severity (info/low/medium/high/critical), source (signals/risk/exec), days (1/3/7)
- 🔄 **Auto-refresh**: Polls `/alerts/history` every 5 seconds
- 📄 **Pagination**: 25/50/100 alerts per page
- 🧪 **Test Alert Button**: Manual trigger (hidden by default, enable with `VITE_SHOW_TEST_ALERT=true`)

**Severity Colors:**

- 🔵 **info/low**: Blue/Gray
- 🟠 **medium/high**: Orange
- 🔴 **critical**: Red

**Usage:**

```bash
cd frontend/panel
npm install
npm run dev

# Optional: Enable test alert button
echo "VITE_SHOW_TEST_ALERT=true" >> .env.local

# Visit: http://localhost:5173 → "Alerts" tab
```

**Live Demo Flow:**

1. High-confidence signal arrives (e.g., BUY BTC confidence 0.85)
2. Auto-trigger fires (PR-37)
3. Alert logged to JSONL
4. Panel polls `/alerts/history`
5. New alert appears in table with unread badge
6. Click "Alerts" tab → badge resets

**API Integration:**

- `GET /alerts/history?limit=300&severity=high&days=7`
- `POST /alerts/trigger` (test button)

**ENV:**

- `VITE_SHOW_TEST_ALERT`: Show test alert button (default: false)

## 📈 Roadmap

**LeviBot v1.4.0** — Production-Ready & Demo-Ready

Kapsamlı yol haritası, stratejik vizyon ve sonraki sprint planları için:
👉 **[ROADMAP_SUMMARY.md](docs/ROADMAP_SUMMARY.md)**

**Highlights:**

- ✅ Sprint 1-7: Core Foundation + Documentation (28 PR merged)
- 🟡 Sprint 8: Alerting & Webhooks (PR-34/35 done, 3 more to go)
- 🔜 Sprint 9: Advanced AI Layer (Feature Store, Ensemble, MLOps)
- 🔜 Sprint 10: SaaS & Monetization (API tiering, Token integration)
- 🎯 Target: v2.0.0 — Autonomous AI + Tokenized SaaS platform

> "Artık kod değil, zekâ deploy ediyoruz." — Baron

## Release Matrix

- **v1.0.0**: Core AI + Risk + Panel + Docker (initial)
- **v1.1.0**: Redis RL + Charts + Prod Compose
- **v1.2.0**: S3 Archiver + E2E Tests
- **v1.3.0**: Build Info Metrics + MinIO + Lifespan
- **v1.4.0**: **Docs & Developer Experience** ✨

**Runtime lifecycle**: FastAPI `lifespan` ile yönetilir (modern API). Eski `@app.on_event("startup")` artık yok; tüm startup/shutdown işleri `lifespan` içinde.

---

## Kurulum

1. Python venv

```
python3 -m venv .venv && source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r backend/requirements.txt
# Raporlar için gerekenler (opsiyonel):
python3 -m pip install pandas pyarrow fastparquet
```

2. ENV ayarları

- Örnekler: `docs/ENV.md` (API host/port, Telegram Bot ve Telethon API kimlikleri, borsa anahtar ENV isimleri)
- Hızlı başlangıç: `cp ENV.example .env` (dosyadaki değerleri kendi ortamınıza göre düzenleyin)

3. Backend API

```
cd backend && uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Alternatif (PATH sorunlarını önlemek için tam yol):

```
./.venv/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload
```

4. Telegram ingest (seçenekler)

```
# Bot API ile (aiogram)
python3 -m backend.src.ingest.telegram_signals

# User‑bot (Telethon) ile (auto‑discover + backfill)
python3 -m telegram.user_client
```

5. Panel (ayrı terminal)

```
cd frontend/panel && npm i && npm run dev
```

6. Dark‑Data Modüllerini Dene (iskele)

```
# On‑chain WS (ENV: ETH_WS veya INFURA_KEY)
python3 -m backend.src.onchain.listener

# MEV arb taraması (örnek çağrı — snapshot dosyaları varsayılır)
python3 -c "from backend.src.mev.arb_scan import scan_once; scan_once(['ETHUSDT','BTCUSDT'])"

# NFT sniper (örnek)
python3 -c "from backend.src.nft.sniper import scan_collection; scan_collection('degods', 150.0, 0.9)"
```

## Kullanım Örnekleri (HTTP)

```
curl -s http://localhost:8000/status | jq
curl -s "http://localhost:8000/events?event_type=SIGNAL_EXT_TELEGRAM" | jq
# Çoklu gün geriye bakış ve metin araması
curl -s "http://localhost:8000/events?days=3&q=reservoir&event_type=NFT_SNIPE_CANDIDATE" | jq
# Belirli gün ve sembol filtresi
curl -s "http://localhost:8000/events?day=2025-09-18&symbol=ETHUSDT&limit=20" | jq

# Paper Order (deterministik, offline)
trace="test-$(date +%s)"
curl -s -X POST "http://127.0.0.1:8000/paper/order?symbol=ETHUSDT&side=buy&notional_usd=10&trace_id=$trace" | jq
# JSONL kanıtı
ls -1 backend/data/logs/*/events-*.jsonl 2>/dev/null || echo "no logs yet"
rg "$trace" backend/data/logs -n || true

# CEX Paper Order (ccxt ticker confirm + fallback)
trace="test-$(date +%s)"
curl -s -X POST \
  "http://127.0.0.1:8000/exec/cex/paper-order?exchange=binance&symbol=ETH/USDT&side=buy&notional_usd=10&trace_id=$trace" | jq
# JSONL kanıtı
rg "$trace" backend/data/logs -n || true

curl -s -X POST http://localhost:8000/start | jq
curl -s -X POST http://localhost:8000/stop -H 'Content-Type: application/json' -d '{"reason":"manual"}' | jq
```

## Yol Haritası (TODO)

- VIP/abonelik: ödeme sağlayıcı entegrasyonu (Stripe/Iyzico) + erişim katmanı
- Telegram reputation → ensemble skorlama ile trade gate’e bağlama
- On‑chain pricing: Uniswap v3 Quoter + token decimals/price cache
- MEV: Flashbots Protect/MEV‑Share; sandwich‑risk defans; likidasyon ve arb simülasyonu
- NFT: koleksiyon floor/trait cache, buy flow (Seaport/Blur), private tx
- Panel: pozisyonlar/PnL, kullanıcı bazlı risk kontrolleri, Trace geliştirmeleri
- CI/CD ve Docker compose; prod konfig ve gizli yönetimi

## Geliştirici Notu

- Proje henüz üretimde değil; modüller MVP iskelet seviyesinde. Logging/rapor/panel altyapısı hazır ve genişlemeye uygun.
- MacOS (arm64) ve Python 3.11+/3.12+ uyumu iyi; 3.13’te bazı paketler için pin gerekebilir. Raporlar için `pandas/pyarrow` kurmayı unutmayın.
- Borsa anahtarları, Telegram kimlikleri ve RPC detaylarını .env üzerinden verin; repoya sır koymayın.

---

## API Uçları (özet)

- GET `/status`: servis durumu
- POST `/start`, `/stop`: bot başlat/durdur
- GET `/config`, POST `/config/reload`, PUT `/config`: konfig okuma/güncelleme
- GET `/events`:
  - Parametreler: `event_type` (CSV), `since_iso`, `limit`, `trace_id`, `day` (YYYY-MM-DD), `days` (1-7), `q` (metin araması), `symbol`
  - Örnek: `/events?days=2&q=ONCHAIN&event_type=ONCHAIN_SIGNAL,MEV_ARB_OPP`
- Telegram: GET `/telegram/signals`, `/telegram/reputation`

## CORS

Panel ve diğer istemciler için CORS açıktır. Varsayılan origin `http://localhost:5173` olup `CORS_ORIGINS` ortam değişkeni ile CSV (ör. `http://localhost:5173,https://panel.example.com`) olarak yapılandırılabilir.

- Strategy: POST `/strategy/twap-rule/start|stop`, GET `/strategy/twap-rule/status`
- Strategy: POST `/strategy/perp-breakout/start|stop`, GET `/strategy/perp-breakout/status`
- GET `/metrics`, `/metrics/prom`: basit metrikler + Prometheus

### Health & Metrics

- Health check:

  ```bash
  curl -s http://127.0.0.1:8000/healthz | jq
  ```

- Prometheus metrics (plaintext):

  ```bash
  curl -s http://127.0.0.1:8000/metrics/prom | head
  ```

- Build info metric:

  ```bash
  curl -s http://127.0.0.1:8000/metrics/prom | grep levibot_build_info
  # → levibot_build_info{version="1.2.0",git_sha="02f4b21",branch="main"} 1.0
  ```

- Prometheus scrape örneği:
  ```yaml
  scrape_configs:
    - job_name: "levibot"
      scrape_interval: 5s
      static_configs:
        - targets: ["host.docker.internal:8000"]
          labels:
            env: "dev"
  ```

### Liveness & Readiness

```bash
curl -s http://127.0.0.1:8000/livez | jq
curl -s http://127.0.0.1:8000/readyz | jq
```

`ETH_HTTP` set'liyse `readyz.ok` JSON‑RPC `eth_blockNumber` ile doğrulanır; yoksa local geliştirmede `ok=true` döner.

### Risk Preview (SL/TP)

```bash
curl -s -X POST "http://127.0.0.1:8000/risk/preview?side=buy&price=100" | jq
# ATR varsa:
curl -s -X POST "http://127.0.0.1:8000/risk/preview?side=buy&price=100&atr=1.2" | jq
```

### Panel — Trades Filters

- Symbol autocomplete, side filtresi (`all|buy|sell`), PnL sütunu, sayfalama (25/50/100/200)
- 5 sn'de bir `/events?event_type=POSITION_CLOSED` poll eder (client-side filtre)
- Çalıştırma: `cd frontend/panel && npm i && npm run dev` → `http://localhost:5173`

### Panel — Signals

- **Signals** sayfasında Telegram mesajı gir → skor al (label + confidence + reasons)
- **Auto-route threshold slider**: sadece önizleme (gerçek emir tetikleme backend'de guard'lı)
- **Recent (10)**: son 10 skorlama kayıt tablosu
- **Add to dataset**: skor sonrası label düzelt → dataset'e ekle
- Panel → `http://localhost:5173` (API `http://localhost:8000` üzerinden proxy)

### Panel — Signals Timeline

- **Geçmiş SIGNAL_SCORED** kayıtlarını listeler (800 kayıt, 5 sn poll)
- **Filtreler**: `label` (all/BUY/SELL/NO-TRADE), `min confidence` (slider 0–0.99), `search` (text contains)
- **Routed badge**: `AUTO_ROUTE_EXECUTED` veya `AUTO_ROUTE_DRYRUN` ile ±120 sn içinde aynı metin başlığı eşleşirse rozet gösterilir:
  - 🟢 **executed**: gerçek paper order tetiklendi
  - 🟡 **dry-run**: sadece dry-run log
  - ⚪ **no**: route edilmedi (guard'lar veya threshold)
- **Sayfalama**: 25/50/100/200 satır/sayfa
- **Client-side join**: backend'e dokunmadan, tarayıcıda iki event tipini eşleştiriyor
- **Real-time**: canlı Telegram + live-tg çalışıyorsa tablo 5 sn'de bir güncellenir

### Monitoring & Alerts (local)

```bash
# API yerelde 8000'de açıkken:
cd ops
docker compose up -d

# Prometheus → http://localhost:9090
# Grafana → http://localhost:3000 (anonymous viewer açık)
# Dashboard: ops/grafana/dashboards/levibot-dashboard.json auto-provisioned

# Hızlı smoke:
curl -s http://127.0.0.1:8000/status > /dev/null
curl -s "http://127.0.0.1:8000/events?limit=2" > /dev/null
curl -s -X POST "http://127.0.0.1:8000/paper/order?symbol=ETHUSDT&side=buy&notional_usd=10" > /dev/null

# Metrik kontrolü:
curl -s http://127.0.0.1:8000/metrics/prom | grep levibot_events_total | head
```

### Signal Scoring (ML)

```bash
# 1) İlk eğitim (TF-IDF + LinearSVC)
source .venv/bin/activate
python -c "from backend.src.ml.signal_model import train_and_save; train_and_save()"
# → backend/artifacts/signal_clf.joblib oluşur (ilk sefer 10 örnekle de çalışır)

# 2) API
./.venv/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload

# 3) Score single message
curl -s -X POST "http://127.0.0.1:8000/signals/score?text=BUY%20BTCUSDT%20@%2060000" | jq
# → {"label":"BUY","confidence":0.62,"reasons":["rule:BUY(1)","ml:BUY(0.xx)"]}

curl -s -X POST "http://127.0.0.1:8000/signals/score?text=avoid%20news%2C%20no%20trade" | jq
# → {"label":"NO-TRADE","confidence":0.58,"reasons":["rule:NO-TRADE(1)","ml:NO-TRADE(0.xx)"]}

# 4) Ingest + Score (logs SIGNAL_INGEST + SIGNAL_SCORED)
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=long%20ETH%20above%202900&source=telegram" | jq

# 5) JSONL kanıtı (SIGNAL_SCORED event)
rg "SIGNAL_SCORED" backend/data/logs -n | tail -3

# 6) Dataset büyütme (zamanla)
echo '{"text":"short BTC at 61000 sl 62500","label":"SELL"}' >> backend/data/signals/labels.jsonl
# re-train:
python -c "from backend.src.ml.signal_model import train_and_save; train_and_save()"
```

**Yol Haritası (Signal)**:

- **Dataset büyütme**: Günlük 20–50 örnek etiketle → haftalık retrain cron job.
- **Confidence kalibrasyonu**: ✅ `CalibratedClassifierCV` ile 0–1 olasılık kalibrasyonu aktif.
- **Feature Engineering**: ✅ TP/SL/size parsing + multi-symbol + channel trust scores.
- **Auto-routing**: ✅ Tamamlandı (guard'lı, dry-run + gerçek tetikleme).
- **Panel**: `/signals` sayfasında canlı skor + timeline; filtre + sıralama.

### Auto-Routing (guard'lı)

```bash
# .env
AUTO_ROUTE_ENABLED=true
AUTO_ROUTE_DRY_RUN=true     # önce dry-run ile doğrula
AUTO_ROUTE_MIN_CONF=0.75
AUTO_ROUTE_EXCH=binance
AUTO_ROUTE_SYMBOL_MAP=BTC:BTC/USDT,ETH:ETH/USDT,SOL:SOL/USDT

# 1) Dry-run akışı (API)
export AUTO_ROUTE_ENABLED=true
export AUTO_ROUTE_DRY_RUN=true
export AUTO_ROUTE_MIN_CONF=0.6
export AUTO_ROUTE_EXCH=binance
export AUTO_ROUTE_SYMBOL_MAP=BTC:BTC/USDT,ETH:ETH/USDT

./.venv/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload

# Skor + dry-run
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=BUY%20BTCUSDT%20@%2060000&source=tg" | jq
# → routed=false, AUTO_ROUTE_DRYRUN eventi loglanır

# JSONL kanıtı
rg "AUTO_ROUTE_DRYRUN|SIGNAL_SCORED" backend/data/logs -n | tail -5

# 2) Gerçek tetikleme (dikkat: paper order oluşturur)
export AUTO_ROUTE_DRY_RUN=false
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=BUY%20BTCUSDT%20@%2060000&source=tg" | jq
# → routed=true, AUTO_ROUTE_EXECUTED + ORDER_NEW + ORDER_FILLED + POSITION_CLOSED eventleri

# JSONL kanıtı
rg "AUTO_ROUTE_EXECUTED|ORDER_NEW|ORDER_FILLED|POSITION_CLOSED" backend/data/logs -n | tail -10
```

**Guard'lar**:

- `AUTO_ROUTE_ENABLED=false` → hiç tetikleme yapılmaz, sadece skor döner.
- `AUTO_ROUTE_DRY_RUN=true` → eşik geçse bile emir gönderilmez, `AUTO_ROUTE_DRYRUN` event'i loglanır.
- `AUTO_ROUTE_MIN_CONF` → confidence bu değerin altındaysa skip edilir.
- `AUTO_ROUTE_SYMBOL_MAP` → sembol dönüşüm haritası (ör. BTC → BTC/USDT).

**Event Akışı** (dry-run=false + eligible):

1. `SIGNAL_INGEST` → metin alındı
2. `SIGNAL_SCORED` → skor + label + confidence
3. `AUTO_ROUTE_EXECUTED` → tetikleme onayı
4. `ORDER_NEW`, `ORDER_PARTIAL_FILL`, `ORDER_FILLED`, `RISK_SLTP`, `POSITION_CLOSED` → paper order akışı

### Live Telegram Ingest (E2E)

```bash
# 1) ENV ayarları
export TELEGRAM_API_ID=123456
export TELEGRAM_API_HASH=your_hash
export TELEGRAM_CHANNELS=@alpha,@beta
export TELEGRAM_MIN_TEXT_LEN=12
export AUTO_ROUTE_ENABLED=true
export AUTO_ROUTE_DRY_RUN=true      # önce dry-run ile test et
export AUTO_ROUTE_MIN_CONF=0.75

# 2) Bağımlılıklar
source .venv/bin/activate
pip install -r backend/requirements.txt

# 3) API başlat (terminal 1)
make run
# veya: ./.venv/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload

# 4) Telegram listener başlat (terminal 2)
make live-tg
# veya: ./.venv/bin/python -m backend.src.ingest.telegram_live

# 5) Kanallara mesaj at → 1-2 sn içinde JSONL'de event akışı:
rg "SIGNAL_INGEST|SIGNAL_SCORED|AUTO_ROUTE" backend/data/logs -n | tail -20

# 6) Gerçek tetikleme (dikkat: paper order oluşturur)
export AUTO_ROUTE_DRY_RUN=false
# live-tg'yi yeniden başlat
```

**Özellikler**:

- ✅ **Telethon** ile belirlenen kanalları dinler (user client, bot token gerekmez)
- ✅ Mesaj alınır → `/signals/ingest-and-score` API'sine POST
- ✅ Guard'lar aktifse (enabled + threshold) → auto-route tetiklenir
- ✅ `TELEGRAM_SESSION` persist edilir (ilk sefer telefon onayı gerekir)
- ✅ Async + aiohttp: non-blocking, düşük latency

**İlk Çalıştırma** (session yoksa):

- `make live-tg` → telefon numarası ister → SMS kodu gir → session kaydedilir
- Sonraki çalıştırmalarda otomatik bağlanır

**JSONL Event Akışı** (örnek):

```
SIGNAL_INGEST → source:telegram, text:"BUY BTCUSDT @ 60000"
SIGNAL_SCORED → label:BUY, confidence:0.82
AUTO_ROUTE_EXECUTED → exchange:binance, symbol:BTC/USDT, side:buy
ORDER_NEW → qty:0.00041667, price:60000
ORDER_PARTIAL_FILL → qty:0.00020833
ORDER_FILLED → qty:0.00041667
RISK_SLTP → sl:58800, tp:61500
POSITION_CLOSED → pnl_usdt:0.0
```

### Feature Engineering (TP/SL/Size + Multi-Symbol)

**Parser**: `backend/src/signals/fe.py`

- Semboller: BTC, ETH, SOL (BTCUSDT, ETH/USDT dahil)
- TP/SL: `tp 62000`, `t/p: 62000`, `take-profit=1.25`, `sl 58500`, `s/l 180`, `stop-loss 29800`
- Size: `size 25`, `qty 0.5`, `notional 100`, `risk 20usd`
- Çoklu sembol: `BUY BTC ETH SOL` → her biri için ayrı değerlendirme

**Autoroute akışı**:

1. `/signals/ingest-and-score` → FE parser çalışır
2. `symbols` varsa FE'den, yoksa eski `parse_symbol()` fallback
3. `size` varsa notional = size, yoksa `AUTO_ROUTE_DEFAULT_NOTIONAL` (25)
4. Çoklu sembol → her biri için ayrı dry-run/execute
5. `AUTO_ROUTE_EXECUTED` event'lerde tp/sl/notional loglanır

**Örnek**:

```bash
# Çoklu sembol + TP/SL/size
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=BUY%20BTC%20ETH%20tp%2062000%20sl%2058500%20size%2030" | jq
# → fe: {symbols: ["BTC/USDT","ETH/USDT"], tp:62000, sl:58500, size:30}
# → routed=true (her sembol için ayrı order)

# JSONL kanıtı
rg "AUTO_ROUTE_EXECUTED|RISK_SLTP" backend/data/logs -n | tail -10
```

**Panel görünürlük**:

- Signals sayfası → skor kartında: `symbols`, `tp/sl/size` gösterilir
- Timeline → FE kolonu: sembollerin ilk ikisi, tp/sl/size özeti

### Dataset & Retrain (Model Güçlendirme)

```bash
# 1) CLI ile veri ekleme
python -m backend.src.ml.ds_tools append "BUY BTC @ 60000 tp 62500" BUY
python -m backend.src.ml.ds_tools append "SELL ETH/USDT 2950" SELL
python -m backend.src.ml.ds_tools append "wait for confirmation" NO-TRADE

# 2) Dataset raporu (sınıf dağılımı)
python -m backend.src.ml.ds_tools report
# → {"total": 13, "class_counts": {"BUY": 5, "SELL": 4, "NO-TRADE": 4}}

# 3) Model retrain (calibrated)
python -m backend.src.ml.retrain
# → backend/artifacts/signal_clf.joblib güncellenir
# → backend/artifacts/metrics.json oluşturulur

# 4) Docker ile retrain (opsiyonel)
docker compose -f ops/docker-compose-cron.yml run --rm retrain

# 5) Cron setup (haftalık - Pazartesi 03:00)
# crontab -e
# 0 3 * * 1  cd /path/to/levibot && bash ops/cron/retrain.sh >> /tmp/levibot_retrain.log 2>&1

# 6) Panel'den veri ekleme
# Signals sayfası → mesaj gir → score → "Add to dataset" kutusu
# → label seç (BUY/SELL/NO-TRADE) → Append → DS_APPEND event loglanır
```

**Özellikler**:

- ✅ **`ds_tools.py`**: `append_label()`, `dump_report()` — CLI + programmatic API
- ✅ **`retrain.py`**: otomatik eğitim + `metrics.json` kayıt
- ✅ **Cron script**: `ops/cron/retrain.sh` — haftalık retrain
- ✅ **Docker Compose**: `ops/docker-compose-cron.yml` — izole retrain environment
- ✅ **Panel UI**: Signals sayfasında "Add to dataset" kutusu → `/ml/dataset/append` API
- ✅ **JSONL event**: `DS_APPEND` → etiketleme aktivitesi

**Workflow**:

1. Live Telegram'dan mesajlar geliyor → skor alıyorlar
2. Yanlış skor alan mesajları Panel'den düzelt → "Add to dataset"
3. Haftada 1 cron çalışıyor → model yeniden eğitiliyor (calibrated)
4. Yeni model artifact'i API restart'inde otomatik yükleniyor
5. Confidence kalitesi artıyor → auto-route false-positive azalıyor

### Security (API Key + Rate Limit)

**Middleware**: `backend/src/infra/sec.py`

- Header: `X-API-Key`, ENV: `API_KEYS=key1,key2` (boşsa auth kapalı)
- Rate limit (sliding window + burst toleransı):
  - `RATE_LIMIT_BY=ip|key`
  - `RATE_LIMIT_WINDOW_SEC=60`, `RATE_LIMIT_MAX=120`, `RATE_LIMIT_BURST=40`
- Korumalı pathler: `SECURED_PATH_PREFIXES=/signals,/exec,/paper`
- Serbest: `/livez`, `/readyz`, `/healthz`, `/metrics/prom`, `/status`, `/events`

**Örnek**:

```bash
# .env
API_KEYS=demo-key-1,demo-key-2
RATE_LIMIT_BY=key
RATE_LIMIT_WINDOW_SEC=60
RATE_LIMIT_MAX=120
RATE_LIMIT_BURST=40
SECURED_PATH_PREFIXES=/signals,/exec,/paper

# Auth
curl -s -X POST "http://127.0.0.1:8000/signals/score?text=BUY" | jq
# → 403 (forbidden)

curl -s -H "X-API-Key: demo-key-1" -X POST "http://127.0.0.1:8000/signals/score?text=BUY" | jq
# → 200 (ok)

# Rate limit (120 istek/60s, burst 40)
for i in {1..130}; do curl -s -o /dev/null -w "%{http_code}\n" -H "X-API-Key: demo-key-1" -X POST "http://127.0.0.1:8000/signals/score?text=BUY"; done
# → ilk 120 → 200, sonrası → 429 (rate limit)
```

**Notlar**:

- ✅ In-memory rate limit (tek replika için ideal; çok replika için Redis gerekir)
- ✅ API_KEYS plaintext (prod için Secrets Manager önerilir)
- ✅ Prefix-bazlı whitelist (granular kota istersen path-level eklenebilir)

### Risk++ (ATR-based SL/TP + Policy)

**Policies**: `conservative`, `moderate`, `aggressive`

- **conservative**: SL=2.0×ATR, TP=1.0×ATR, cooldown=45s
- **moderate**: SL=1.5×ATR, TP=1.5×ATR, cooldown=30s
- **aggressive**: SL=1.0×ATR, TP=2.0×ATR, cooldown=20s

**Öncelik**: FE hint (tp/sl metinden) > ATR türetme

**ENV**:

```bash
RISK_POLICY=moderate             # conservative | moderate | aggressive
RISK_ATR_LOOKBACK=14             # sentetik ATR için varsayılan pencere
RISK_R_MULT=1.0                  # ATR çarpanı (policy ile override edilir)
RISK_MAX_NOTIONAL=250            # route başına üst limit (usd)
RISK_MIN_NOTIONAL=5              # alt limit (usd)
```

**Event'ler**:

- `RISK_SLTP` → `{sl, tp, atr, policy, source}`
  - `source="hint"`: FE'den gelen tp/sl kullanıldı
  - `source="atr"`: Policy+ATR ile türetildi

**Örnek**:

```bash
# Policy aggressive + FE hint yoksa ATR türet
export RISK_POLICY=aggressive
export RISK_MIN_NOTIONAL=10
export RISK_MAX_NOTIONAL=100

# Dry-run (BUY)
export AUTO_ROUTE_ENABLED=true
export AUTO_ROUTE_DRY_RUN=true
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=BUY%20ETHUSDT%20size%2040" | jq
# → RISK_SLTP: policy=aggressive, source=atr

# FE hint önceliği (SELL)
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=SELL%20BTC%20tp%2062000%20sl%2058500" | jq
# → RISK_SLTP: source=hint, sl=58500, tp=62000

# Notional clamp
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=BUY%20SOL%20size%20500" | jq
# → notional clamped to 100 (RISK_MAX_NOTIONAL)

# JSONL kanıtı
rg "RISK_SLTP" backend/data/logs -n | tail -5
```

**Panel**: Signals sayfasında policy selector (görsel - server ENV'i kullanır)

### Runtime Risk Policy Switch

**Endpoints**:

- `GET /risk/policy` → `{current, choices, multipliers, cooldown_sec}`
- `PUT /risk/policy` body: `{"name":"aggressive"}` → anında geçerli

**Panel**: Signals sayfasında **Risk Policy** selector + **Apply** button

- Dropdown'dan policy seç → Apply → server'da runtime değişir
- Process memory'de tutuluyor (restart'ta ENV'e geri döner)

**Güvenlik**: `/risk` prefixini `SECURED_PATH_PREFIXES` içine ekleyebilirsin (API key + rate limit)

**Örnek**:

```bash
# GET current policy
curl -s http://127.0.0.1:8000/risk/policy | jq
# → {current:"moderate", choices:["conservative","moderate","aggressive"], multipliers:{sl:1.5,tp:1.5}, cooldown_sec:30}

# PUT (gerekirse API key başlığı ekle)
curl -s -X PUT http://127.0.0.1:8000/risk/policy \
  -H 'Content-Type: application/json' \
  -d '{"name":"aggressive"}' | jq
# → {ok:true, current:"aggressive"}

# Paper akışında SL/TP farkı
export AUTO_ROUTE_ENABLED=true
export AUTO_ROUTE_DRY_RUN=true
curl -s -X POST "http://127.0.0.1:8000/signals/ingest-and-score?text=BUY%20BTCUSDT%20size%2030" | jq
# → RISK_SLTP.policy şimdi aggressive

# JSONL kanıtı
rg "RISK_POLICY_CHANGED" backend/data/logs -n | tail -3
```

**Event**: `RISK_POLICY_CHANGED` → `{name, sl_mult, tp_mult, cooldown_sec}`

---

## MEV / NFT / L2 Mini-Suite

**Offline-safe**: API anahtarları yoksa sentetik fallback kullanır; varsa gerçek veriye bağlanır.

### DEX Quote & Tri-Arb Scan

**Endpoints**:

- `GET /dex/quote?sell=ETH&buy=USDC&amount=0.1&chain=ethereum`
- `GET /mev/tri-scan?a=ETH&b=USDC&c=WBTC&amount=0.1&chain=ethereum`

**0x Integration**: `ZEROX_API_KEY` varsa gerçek quote; yoksa offline fallback (ETH→USDC=2000, diğer=1.0)

**Örnek**:

```bash
# DEX quote
curl -s "http://127.0.0.1:8000/dex/quote?sell=ETH&buy=USDC&amount=0.1" | jq
# → {ok:true, price:2000.0, fallback:true}

# Tri-arb scan (ETH→USDC→WBTC→ETH)
curl -s "http://127.0.0.1:8000/mev/tri-scan?a=ETH&b=USDC&c=WBTC&amount=0.1" | jq
# → {ok:true, route:["ETH","USDC","WBTC","ETH"], edge:-0.0001, legs:{...}}

# JSONL kanıtı
rg "DEX_QUOTE|MEV_TRI" backend/data/logs -n | tail -5
```

**Event'ler**: `DEX_QUOTE`, `MEV_TRI`

### NFT Floor & Snipe Plan

**Endpoints**:

- `GET /nft/floor?collection=miladymaker`
- `GET /nft/snipe/plan?collection=miladymaker&budget_usd=300&discount_pct=12`

**Reservoir Integration**: `RESERVOIR_API_KEY` varsa gerçek floor; yoksa offline fallback (42.0 USD)

**Örnek**:

```bash
# Floor price
curl -s "http://127.0.0.1:8000/nft/floor?collection=miladymaker" | jq
# → {ok:true, name:"miladymaker", floor:42.0, fallback:true}

# Snipe plan (floor'dan %12 indirimli hedef)
curl -s "http://127.0.0.1:8000/nft/snipe/plan?collection=miladymaker&budget_usd=300&discount_pct=12" | jq
# → {ok:true, collection:"miladymaker", target_usd:36.96, budget_usd:300, discount_pct:12, floor:42.0}

# JSONL kanıtı
rg "NFT_FLOOR|NFT_SNIPE_PLAN" backend/data/logs -n | tail -5
```

**Event'ler**: `NFT_FLOOR`, `NFT_SNIPE_PLAN`

### L2 Yield Tracker

**Endpoint**: `GET /l2/yields`

**YAML-based**: `backend/configs/yields.yaml` içinden okur (Arbitrum/Base/Optimism protokol APR'leri)

**Örnek**:

```bash
# L2 yields
curl -s "http://127.0.0.1:8000/l2/yields" | jq
# → {ok:true, chains:[{name:"arbitrum", protocols:[{name:"gmx", pool:"GLP", apr:12.4}, ...]}, ...]}

# JSONL kanıtı
rg "L2_YIELDS" backend/data/logs -n | tail -3
```

**Event**: `L2_YIELDS`

**ENV**:

```bash
# DEX / MEV
ZEROX_API_URL=https://api.0x.org/swap/v1/quote
ZEROX_API_KEY=
DEX_DEFAULT_CHAIN=ethereum    # ethereum | polygon | arbitrum

# NFT
RESERVOIR_API_URL=https://api.reservoir.tools
RESERVOIR_API_KEY=
```

**Test**:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q backend/tests/test_mev_quote_tri.py backend/tests/test_nft_floor_plan.py backend/tests/test_l2_yields.py
# → 11 passed
```

### Panel Mini-Cards (DEX / NFT / L2)

**3 yeni kart**: Dashboard'da görsel olarak MEV/NFT/L2 verilerini gösterir.

**DEXQuoteCard**:

- Input: `sell` (ETH), `buy` (USDC), `amount` (0.1)
- Output: Price (offline fallback: 2000, gerçek 0x API varsa live)
- Auto-fetch on mount

**NFTFloorCard**:

- Input: `collection` (miladymaker)
- Output: Floor price (offline fallback: 42 USD, gerçek Reservoir API varsa live)
- Snipe Plan: `budget`, `discount%` → target price

**L2YieldsCard**:

- `backend/configs/yields.yaml`'dan okur
- Tablo: Chain / Protocol / Pool / APR%
- Refresh button

**Kullanım**:

```bash
# Backend
make run

# Frontend
cd frontend/panel && npm i && npm run dev
# → http://localhost:5173
# → 3 yeni kart görünür (DEX Quote, NFT Floor, L2 Yields)
```

**Offline-safe**: API anahtarları yoksa sentetik fallback değerleri gösterir.

---

## Distributed Rate Limit (Redis)

**Redis-backed token bucket** rate limiter for multi-instance deployments.

**ENV**:

```bash
REDIS_URL=redis://localhost:6379/0
RL_WINDOW_SEC=60
RL_MAX=120
RL_BURST=40
```

**Davranış**:

- `REDIS_URL` varsa → Redis token-bucket (Lua script, atomic)
- `REDIS_URL` yoksa → In-memory fallback (thread-safe, single instance)

**Özellikler**:

- ✅ **Distributed**: Çok replika arasında paylaşılan limit
- ✅ **Atomic**: Lua script ile race condition yok
- ✅ **Burst tolerance**: Kısa süreli spike'lara tolerans
- ✅ **Auto-expire**: Redis TTL ile otomatik temizlik
- ✅ **Graceful fallback**: Redis yoksa in-memory'ye düşer

**Kullanım**:

```bash
# Redis başlat (Docker)
docker run -d --name redis -p 6379:6379 redis:7

# ENV
export REDIS_URL=redis://localhost:6379/0
export RL_WINDOW_SEC=60
export RL_MAX=20
export RL_BURST=5

# API
make run

# Throttle testi (40 istek)
for i in {1..40}; do curl -s -o /dev/null -w "%{http_code} " http://127.0.0.1:8000/status; done
# → 200 200 200 ... 429 429 429
```

**Test**:

```bash
# Fallback mode (Redis yok)
unset REDIS_URL
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q backend/tests/test_redis_rl.py::test_fallback_allow
# → 1 passed

# Redis mode (Redis var)
export REDIS_URL=redis://localhost:6379/0
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q backend/tests/test_redis_rl.py
# → 3 passed (veya 1 skipped if no Redis)
```

**Metrics**:

```bash
cat backend/artifacts/metrics.json
# {
#   "ts": 1696339200.123,
#   "model_path": "backend/artifacts/signal_clf.joblib",
#   "note": "calibrated LinearSVC (Platt), trained on labels.jsonl"
# }
```

## Event Şemaları

```json
// ONCHAIN_SIGNAL
{"ts":"...","event_type":"ONCHAIN_SIGNAL","payload":{"chain":"ethereum","kind":"univ3_pool_created|erc20_transfer","tx_hash":"0x..","block":12345}}

// MEV_RISK
{"event_type":"MEV_RISK","payload":{"symbol":"ETHUSDT","kind":"sandwich_hazard","est_bps":12.3}}

// MEV_ARB_OPP
{"event_type":"MEV_ARB_OPP","payload":{"symbol":"ETHUSDT","edge_bps":9.1,"route":[{"bps":9.1}]}}

// MEV_LIQ_OPP
{"event_type":"MEV_LIQ_OPP","payload":{"protocol":"aave_v3","market":"USDC","account":"0x..","health":1.03,"est_profit_usd":42}}

// NFT_SNIPE_CANDIDATE
{"event_type":"NFT_SNIPE_CANDIDATE","payload":{"collection":"cool-cats","tokenId":"123","ask":120,"floor":125,"rare_score":0.9,"spread_pct":-4.0,"provider":"reservoir","listing_id":"..."}}
```

## Config Örnekleri (ek)

```yaml
# backend/configs/onchain.yaml
chains:
  - name: ethereum
    rpc_ws: wss://mainnet.infura.io/ws/v3/${INFURA_KEY}
    rpc_http: https://mainnet.infura.io/v3/${INFURA_KEY}
    start_block: latest
    topics:
      [
        uniswap_v3_pool_created,
        uniswap_v3_swap,
        erc20_transfer,
        aave_liquidation,
      ]
cex_hot_wallets: [binance, coinbase, kraken]
stable_symbols: [USDT, USDC, DAI]
thresholds: { whale_usd: 500000, new_pool_min_liq_usd: 150000 }

# backend/configs/mev.yaml
defensive: { enable_sandwich_risk: true, protect_provider: flashbots }
arb: { enable: true, max_hops: 2, min_edge_bps: 8 }
liquidations: { enable: true, protocols: [aave_v3, compound_v3] }

# backend/configs/nft.yaml
market: { providers: [reservoir, opensea, blur] }
filters: { min_floor_usd: 100, rare_score_min: 0.9, max_spread_pct: 2.0 }
sniper:
  {
    enabled: true,
    max_notional_usd: 800,
    private_tx: true,
    wallet_label: "nft_vault_1",
  }
```

## Hızlı Smoke Akışı

```bash
# ENV (örnek)
export INFURA_KEY=xxxxx
export ETH_WS=wss://mainnet.infura.io/ws/v3/${INFURA_KEY}
export ETH_HTTP=https://mainnet.infura.io/v3/${INFURA_KEY}
export RESERVOIR_API_KEY=xxxxx

# Backend
uvicorn backend.src.app.main:app --reload

# On-chain
python3 -m backend.src.onchain.listener
curl -s 'http://localhost:8000/events?event_type=ONCHAIN_SIGNAL&limit=5' | jq

# MEV (scheduler 20. saniye)
sleep 70
curl -s 'http://localhost:8000/events?event_type=MEV_ARB_OPP&limit=3' | jq

# NFT
python3 - <<'PY'
from backend.src.nft.sniper import scan_collection
scan_collection('cool-cats', floor_min_usd=100, rare_min=0.8)
PY
curl -s 'http://localhost:8000/events?event_type=NFT_SNIPE_CANDIDATE&limit=3' | jq
```

## Sorun Giderme (Troubleshooting)

- Uvicorn import hataları: eksik stub registry (TWAP/BREAKOUT) ve `pandas` çözüldü; sorun devam ederse venv’i temizleyip kurun.
- WebSocket bağlanmıyor: `INFURA_KEY`/WSS erişimi ve kurum ağı engellerini kontrol edin.
- `/events` boş: önce producer’ları (listener/snapshot/sniper) çalıştırın; sonra tekrar sorgulayın.
- Reservoir 401/429: `RESERVOIR_API_KEY` ve rate-limit; daha düşük frekans deneyin.
- DuckDB dosya kilidi: aynı parquet’i birden fazla job yazmasın; scheduler tek işte yazsın.

## Güvenlik ve Operasyon

- MEV defans: Protect/MEV‑Share ile private mempool, kendi işlemlerini sandwich’e kapat.
- OpSec: API anahtarları/.env’ler repo dışı; HSM/keystore önerilir. `nft_vault_1` için ayrı cüzdan.
- Simülasyon: Tenderly/Foundry ile dry‑run; NFT’de wash‑trade tespiti için blacklist/heuristic.
- Yasal: Bölgesel düzenlemeler ve pazar yeri ToS’lerine uyum.

## 🧯 Troubleshooting

### 1) `uvicorn: command not found`

- Neden: venv aktif değil.
- Çözüm:
  ```bash
  source .venv/bin/activate
  # veya tam yol
  ./.venv/bin/uvicorn backend.src.app.main:app --reload
  ```

### 2) CORS / Panel istekleri bloklanıyor

- Belirti: Panel `/events` fetch error.
- Çözüm: `.env` içine izinli origin ekle:
  ```ini
  CORS_ORIGINS=http://localhost:5173
  ```
  API restart sonrası tekrar deneyin.

### 3) JSONL dosyaları görünmüyor

- Belirti: `backend/data/logs/*/events-*.jsonl` bulunamadı.
- Çözüm: Önce bir işlem tetikle:
  ```bash
  trace="test-$(date +%s)"
  curl -s -X POST \
    "http://127.0.0.1:8000/paper/order?symbol=ETHUSDT&side=buy&notional_usd=10&trace_id=$trace" | jq
  ```
  Ardından:
  ```bash
  ls -1 backend/data/logs/*/events-*.jsonl 2>/dev/null || echo "no logs yet"
  rg "$trace" backend/data/logs -n || true
  ```

### 4) `jq` / `rg` yok

- macOS: `brew install jq ripgrep fd`
- Ubuntu/Debian: `sudo apt install -y jq ripgrep fd-find`

### 5) Port çakışması (8000 kullanılıyor)

- Çözüm:
  ```bash
  ./.venv/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8010 --reload
  ```

### 6) Pytest plugin çakışması

- Belirti: “weird plugin import errors”.
- Çözüm:
  ```bash
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q
  # CI'da zaten setli.
  ```

### 7) Health & Metrics görünmüyor

- Health:
  ```bash
  curl -s http://127.0.0.1:8000/healthz | jq
  ```
- Prometheus metrics:
  ```bash
  curl -s http://127.0.0.1:8000/metrics/prom | head
  ```

### Panel — Trades

<p align="center">
  <img src="assets/panel-trades.png" alt="Trades Feed" width="720"/>
  </p>

# 🚀 LeviBot Enterprise Deployment Guide

## Production-Ready AI Trading Platform

### 📋 Önkoşullar

**Sistem Gereksinimleri**

- Ubuntu 22.04+ / Debian 12 / macOS (dev)
- Docker 24+ & Docker Compose
- 4 vCPU / 8 GB RAM (minimum dev)
- 20 GB+ NVMe disk
- Domain (opsiyonel) + reverse proxy

**Gerekli Bilgiler**

- Exchange API keys (testnet/paper trading için)
- Telegram Bot Token
- Telegram Admin Chat ID

---

## 🏗️ Mimari Özet

```
┌─────────────┐
│   Telegram  │
│  Bot + Mini │
│     App     │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│           FastAPI Panel (8080)              │
│  • REST API                                 │
│  • WebSocket feed                           │
│  • Prometheus metrics                       │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│         Event Bus (Redis Streams)           │
│  • signals.*                                │
│  • orders.*                                 │
│  • alerts.*                                 │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│      Strategy Orchestrator + Workers        │
│  • Ingest (WS/REST)                        │
│  • Feature Builder                          │
│  • Signal Engine (ML + Rules)              │
│  • Paper Executor                           │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│           Storage Layer                     │
│  • ClickHouse (timeseries)                 │
│  • Redis (hot cache)                        │
│  • TimescaleDB (trades/equity)             │
└─────────────────────────────────────────────┘
```

---

## 🔧 Kurulum Adımları

### 1) Repository Klonla

```bash
git clone https://github.com/yourorg/levibot.git
cd levibot
```

### 2) Environment Dosyasını Hazırla

```bash
cp .env.example .env
```

**`.env` içeriği:**

```bash
# ============================================
# Core Configuration
# ============================================
ENV=paper
TZ=Europe/Istanbul
LOG_LEVEL=INFO

# ============================================
# Redis (Event Bus + Cache)
# ============================================
REDIS_URL=redis://redis:6379/0

# ============================================
# ClickHouse (Analytics)
# ============================================
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_HTTP_PORT=8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DB=levibot

# ============================================
# TimescaleDB (Trades)
# ============================================
PG_DSN=postgresql://postgres:postgres@timescaledb:5432/levibot

# ============================================
# API & Panel
# ============================================
PANEL_PORT=8080
API_AUTH_SECRET=change_me_to_secure_random_string_min_32_chars
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# ============================================
# Telegram Integration
# ============================================
TG_BOT_TOKEN=123456:ABCDEF_your_bot_token_here
TG_ADMIN_IDS=123456789,987654321
TG_MINI_APP_URL=http://localhost:8080

# ============================================
# Exchange Configuration
# ============================================
EXCHANGE=binance
MARKET_TYPE=futures
BINANCE_KEY=your_testnet_api_key
BINANCE_SECRET=your_testnet_api_secret
BINANCE_TESTNET=true

# ============================================
# ML Model
# ============================================
MODEL_VERSION=1.0.0
MODEL_STAGE=production

# ============================================
# Observability
# ============================================
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin

# ============================================
# Build Info
# ============================================
BUILD_VERSION=1.0.0
BUILD_SHA=local
BUILD_BRANCH=main
```

### 3) Sistem Ayağa Kaldır

```bash
# Tüm servisleri başlat
make up

# Durum kontrol
make ps

# Logları izle
make logs
```

### 4) Health Check

```bash
# Panel API
curl http://localhost:8080/healthz

# Prometheus metrics
curl http://localhost:9100/metrics  # Signal engine
curl http://localhost:9101/metrics  # Executor

# ClickHouse
curl http://localhost:8123/ping

# Redis
docker exec -it levibot-redis redis-cli ping
```

---

## 📊 Monitoring & Observability

### Grafana Dashboard

1. Aç: `http://localhost:3000`
2. Login: `admin` / `admin` (değiştir!)
3. Datasource otomatik eklenir (Prometheus)
4. Dashboard import et: `docker/grafana/dashboards/pnl.json`

**İzlenecek Metrikler:**

- `levibot_portfolio_equity_usd` - Portfolio değeri
- `levibot_portfolio_daily_pnl_usd` - Günlük PnL
- `levibot_portfolio_drawdown_pct` - Drawdown
- `levibot_trades_total` - Trade sayısı
- `levibot_signals_generated_total` - Sinyal sayısı
- `levibot_policy_kill_switch_active` - Kill switch durumu

### Telegram Bot

```
/start - Ana menü
/status - Sistem durumu
/pnl - PnL özeti
/killswitch - Acil durdurma (admin)
/strategies - Strateji istatistikleri
```

**Mini App:**

- Telegram'da `/start` → "🎛️ Control Panel" butonu
- Real-time equity curve
- Position monitoring
- Kill switch toggle
- Daily stats reset

---

## 🔒 Güvenlik

### Production Checklist

- [ ] `.env` dosyasını `.gitignore`'a ekle
- [ ] `API_AUTH_SECRET` değiştir (min 32 karakter)
- [ ] Telegram Bot token'ı güvenli tut
- [ ] Exchange API keys'i read-only yap (paper trading için)
- [ ] Grafana admin şifresini değiştir
- [ ] ClickHouse için şifre belirle
- [ ] CORS origins'i production domain'e güncelle
- [ ] Rate limiting ekle (Nginx/Traefik)
- [ ] SSL/TLS sertifikası kur (Let's Encrypt)
- [ ] Firewall kuralları ayarla
- [ ] Backup stratejisi belirle

### Telegram WebApp Security

Mini App, Telegram'ın `initData` HMAC doğrulaması kullanır:

```python
# backend/src/app/auth.py
def verify_telegram_webapp(init_data: str, bot_token: str) -> bool:
    # HMAC-SHA256 doğrulaması
    # Telegram docs: https://core.telegram.org/bots/webapps
    pass
```

---

## 🎯 Canary Deployment (Paper Trading)

### Aşama 1: Single Symbol (48 saat)

```yaml
# configs/config.yaml
symbols: ["BTCUSDT"]
timeframe: "1m"

risk:
  per_trade_risk: 0.002
  daily_dd_stop: 0.03
  cooldown_minutes: 10

signals:
  engine: "ml_then_rules"
  proba_entry: 0.58
```

**Gözlem:**

- Telegram alerts akıyor mu?
- Equity curve smooth mu?
- Drawdown limitleri çalışıyor mu?
- Kill switch test et

### Aşama 2: Multi-Symbol (7 gün)

```yaml
symbols: ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
```

**Gözlem:**

- Symbol correlation
- Position sizing
- Exposure management
- Win rate per symbol

### Aşama 3: Full Universe (30 gün)

```yaml
symbols: core # 10 core + 14 tier2
```

**Gözlem:**

- Sharpe ratio
- Max drawdown
- Recovery time
- Strategy performance

---

## 📦 Backup & Recovery

### ClickHouse Backup

```bash
# Manual backup
docker exec levibot-clickhouse clickhouse-client -q \
  "BACKUP DATABASE levibot TO Disk('backups', 'backup_$(date +%Y%m%d).zip')"

# Restore
docker exec levibot-clickhouse clickhouse-client -q \
  "RESTORE DATABASE levibot FROM Disk('backups', 'backup_20250113.zip')"
```

### Redis Backup

```bash
# AOF persistence aktif (otomatik)
# Manual snapshot
docker exec levibot-redis redis-cli BGSAVE

# Backup dosyası: /data/dump.rdb
```

### Volume Backup

```bash
# Stop services
make down

# Backup volumes
docker run --rm -v levibot_ch-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/clickhouse_$(date +%Y%m%d).tar.gz /data

# Restore
docker run --rm -v levibot_ch-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/clickhouse_20250113.tar.gz -C /
```

---

## 🔧 Troubleshooting

### Panel Başlamıyor

```bash
# Logları kontrol et
docker logs levibot-panel

# Health check
docker exec levibot-panel wget -qO- http://localhost:8080/healthz

# Dependencies
docker ps | grep -E "(redis|clickhouse|timescaledb)"
```

### WebSocket Bağlantı Kesiliyor

```bash
# Ingest logs
docker logs levibot-ingest

# Redis connection
docker exec levibot-redis redis-cli PING

# Network
docker network inspect levibot_default
```

### Signals Gelmiyor

```bash
# Feature builder çalışıyor mu?
docker logs levibot-feature

# Signal engine metrics
curl http://localhost:9100/metrics | grep signals_generated

# Policy engine durumu
curl http://localhost:8080/policy/status
```

### ClickHouse Slow Queries

```sql
-- Query log
SELECT
    query_duration_ms,
    query,
    user
FROM system.query_log
WHERE type = 'QueryFinish'
  AND query_duration_ms > 1000
ORDER BY query_duration_ms DESC
LIMIT 10;

-- Optimize tables
OPTIMIZE TABLE levibot.ohlcv FINAL;
```

---

## 📈 Scaling to Production

### Horizontal Scaling

```yaml
# docker-compose.yml
signal:
  deploy:
    replicas: 3 # Symbol sharding
  environment:
    SYMBOL_SHARD: "${HOSTNAME}"

executor:
  deploy:
    replicas: 2
```

### Load Balancing

```nginx
# nginx.conf
upstream panel_backend {
    least_conn;
    server panel-1:8080;
    server panel-2:8080;
    server panel-3:8080;
}
```

### Database Sharding

```yaml
# ClickHouse cluster
clickhouse-01:
  image: clickhouse/clickhouse-server
  environment:
    CLICKHOUSE_CLUSTER: levibot_cluster

clickhouse-02:
  image: clickhouse/clickhouse-server
  environment:
    CLICKHOUSE_CLUSTER: levibot_cluster
```

---

## 🎓 Best Practices

### Development Workflow

```bash
# Local development
make dev-up      # Start with hot-reload
make test        # Run tests
make lint        # Check code quality

# Build & test
make build       # Build Docker images
make smoke-test  # Quick integration test

# Deploy
make deploy-staging
make deploy-prod
```

### Configuration Management

```bash
# Version control
git tag v1.0.0
git push origin v1.0.0

# Config snapshots
make snapshot-config  # Saves to ops/config-snapshots/

# Rollback
make rollback-config --version=v0.9.0
```

### Monitoring Alerts

```yaml
# prometheus/alerts.yml
groups:
  - name: levibot
    rules:
      - alert: HighDrawdown
        expr: levibot_portfolio_drawdown_pct > 0.05
        for: 5m
        annotations:
          summary: "Drawdown > 5%"

      - alert: KillSwitchActive
        expr: levibot_policy_kill_switch_active == 1
        annotations:
          summary: "Kill switch activated"

      - alert: NoSignalsGenerated
        expr: rate(levibot_signals_generated_total[10m]) == 0
        for: 10m
        annotations:
          summary: "No signals in 10 minutes"
```

---

## 📚 Additional Resources

- **Architecture**: `docs/ARCHITECTURE.md`
- **ML Pipeline**: `docs/ML_PIPELINE.md`
- **API Reference**: `http://localhost:8080/docs` (Swagger)
- **Telegram Bot**: `docs/TELEGRAM.md`
- **Contributing**: `CONTRIBUTING.md`

---

## 🆘 Support

- **Issues**: GitHub Issues
- **Telegram**: @levibot_support
- **Email**: support@levibot.ai

---

**Built with 💙 by LeviBot Team**

# ✈️ LeviBot Enterprise - Preflight Checklist

> **48 saatlik canary run öncesi son kontroller**

---

## ✅ Zorunlu Kontroller

### 1. Environment Configuration

- [ ] `.env` dosyası oluşturuldu (`cp ENV.levibot.example .env`)
- [ ] `TG_BOT_TOKEN` dolduruldu (BotFather'dan alındı)
- [ ] `TG_ADMIN_CHAT_ID` dolduruldu (userinfobot'tan öğrenildi)
- [ ] `MEXC_API_KEY` & `MEXC_SECRET` credentials
- [ ] `API_AUTH_SECRET` en az 32 karakter
- [ ] `TZ=Europe/Istanbul` set edildi
- [ ] `.env` dosyası `.gitignore`'da (commit edilmeyecek)

### 2. Infrastructure

- [ ] Docker Desktop çalışıyor
- [ ] Disk'te en az 10GB boş alan var
- [ ] Port'lar boş: 8080, 9100, 9101, 6379, 8123, 9090, 3000, 5173
- [ ] ClickHouse init SQL'leri hazır (`backend/sql/*.sql`)
- [ ] Prometheus config hazır (`ops/prometheus/*.yml`)

### 3. Risk Management

- [ ] `PER_TRADE_RISK ≤ 0.003` (0.3% max risk per trade)
- [ ] `DAILY_DD_STOP = 0.03` (3% günlük drawdown limiti)
- [ ] `MIN_CONFIDENCE ≥ 0.55` (minimum sinyal güveni)
- [ ] `MAX_DAILY_TRADES = 50` (günlük trade limiti)
- [ ] `COOLDOWN_MINUTES = 10` (trade arası bekleme)

### 4. Security

- [ ] Kill-switch endpoint aktif (`/policy/killswitch`)
- [ ] HMAC authentication Mini App için hazır
- [ ] Rate limiting aktif (API_KEYS set edildi)
- [ ] Audit logging ClickHouse'a yazıyor

### 5. Monitoring

- [ ] Healthcheck endpoint'leri hazır (`/healthz`, `/metrics`)
- [ ] Prometheus scrape config doğru
- [ ] Grafana dashboard'lar yüklendi
- [ ] Alert rules tanımlı (`ops/prometheus/alerts.yml`)

---

## 🚀 Tek Tuş Başlatma

```bash
# Sistemi başlat
make up

# Durum kontrolü
make ps

# Logları izle
make logs
```

---

## 🔎 Smoke Test (5 dakika)

### Panel API

```bash
curl -sf http://localhost:8080/healthz && echo "✓ Panel API OK"
```

### Signal Engine Metrics

```bash
curl -s http://localhost:9100/metrics | head -20
```

### Executor Metrics

```bash
curl -s http://localhost:9101/metrics | head -20
```

### Redis

```bash
docker exec -it $(docker ps -qf name=redis) redis-cli ping
# Beklenen: PONG
```

### ClickHouse

```bash
docker exec -it $(docker ps -qf name=clickhouse) \
  clickhouse-client -q "SHOW TABLES FROM levibot"
# Beklenen: ohlcv, signals, orders, portfolio_snapshots, vb.
```

### Prometheus

```bash
curl -s http://localhost:9090/-/healthy
# Beklenen: Prometheus is Healthy.
```

### Grafana

```bash
curl -s http://localhost:3000/api/health | jq
# Beklenen: {"database": "ok", "version": "..."}
```

---

## 📊 İlk 5 Dakikada Görmemiz Gerekenler

### 1. Telegram Bot

- ✅ `/start` komutu yanıt veriyor
- ✅ "LeviBot Control Online" mesajı geliyor
- ✅ Mini App butonu çalışıyor
- ✅ `/status` komutu sistem durumunu gösteriyor

### 2. Grafana Dashboards

- ✅ Equity curve paneli yüklendi
- ✅ Signal performance metrikleri geliyor
- ✅ System health göstergeleri aktif
- ✅ Trading metrics görünür

### 3. Prometheus Targets

```bash
# Tüm target'lar UP olmalı
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

### 4. ClickHouse Data Flow

```bash
# Son 10 dakikada OHLCV verisi gelmiş mi?
docker exec -it $(docker ps -qf name=clickhouse) clickhouse-client -q \
  "SELECT count(*) FROM levibot.ohlcv WHERE timestamp > now() - INTERVAL 10 MINUTE"
# Beklenen: > 0
```

### 5. Mini App

- ✅ http://localhost:5173 açılıyor
- ✅ Equity curve grafiği render oluyor
- ✅ Recent signals listesi geliyor
- ✅ Kill-switch butonu çalışıyor

---

## 🧯 İlk 24 Saat - En Sık Görülen Sorunlar

### 1. WebSocket Disconnect Spam

**Belirti:** Sürekli reconnect logları
**Çözüm:**

```bash
# Logları kontrol et
make logs-signal | grep -i "websocket\|disconnect"

# Exchange testnet mi kontrol et
grep BINANCE_TESTNET .env
# true olmalı
```

### 2. PnL Grafiği Düz Çizgi

**Belirti:** Equity curve hareket etmiyor
**Çözüm:**

```bash
# Sinyal eşiğini düşür
# .env içinde:
MIN_CONFIDENCE=0.55  # 0.58'den düşür
COOLDOWN_MINUTES=5   # 10'dan düşür

# Restart
make restart
```

### 3. Telegram Komutları Sessiz

**Belirti:** Bot yanıt vermiyor
**Çözüm:**

```bash
# Bot loglarını kontrol et
make logs-bot

# Token'ı doğrula
grep TG_BOT_TOKEN .env

# Bot'u restart et
docker compose -f docker-compose.enterprise.yml restart telegram_bot
```

### 4. ClickHouse Tablolar Boş

**Belirti:** Sorgu 0 satır döndürüyor
**Çözüm:**

```bash
# Ingest servisi çalışıyor mu?
make ps | grep signal

# Logları kontrol et
make logs-signal | grep -i "clickhouse\|insert"

# Manuel test
docker exec -it $(docker ps -qf name=clickhouse) clickhouse-client -q \
  "INSERT INTO levibot.portfolio_snapshots (timestamp, equity, cash, positions_value, unrealized_pnl, realized_pnl, daily_pnl, total_pnl, num_positions) VALUES (now(), 10000, 10000, 0, 0, 0, 0, 0, 0)"
```

### 5. CPU %100

**Belirti:** Sistem yavaşladı
**Çözüm:**

```bash
# Resource kullanımını kontrol et
make stats

# Feature builder interval'ı artır
# .env içinde:
FEATURE_UPDATE_INTERVAL=60  # 30'dan artır

# Restart
make restart
```

### 6. Kill-Switch Tepki Yok

**Belirti:** Kill-switch basıldı ama trade'ler devam ediyor
**Çözüm:**

```bash
# Executor loglarını kontrol et
make logs-executor | grep -i "kill\|switch"

# Redis'te key var mı?
docker exec -it $(docker ps -qf name=redis) redis-cli GET levibot:killswitch

# Manuel set et
docker exec -it $(docker ps -qf name=redis) redis-cli SET levibot:killswitch 1
```

---

## 📈 48 Saatlik Canary - Kabul Kriterleri

### Performance Metrics

- ✅ **Max Drawdown ≤ 3%** (paper mode)
- ✅ **Win Rate ≥ 52%** veya **Avg Win / Avg Loss ≥ 1.3x**
- ✅ **Slippage ≤ 5 bps** (paper executor)
- ✅ **Signal Throughput:** 20-40 trade/48h (BTC/ETH/SOL 1m)
- ✅ **Data Completeness:** OHLCV dakikalık eksik < 3

### System Health

- ✅ **Uptime ≥ 99%** (max 15 dakika downtime)
- ✅ **Error Rate < 0.1%** (total requests)
- ✅ **Latency p95 < 5s** (signal processing)
- ✅ **Memory Usage < 80%** (tüm servisler)
- ✅ **Disk Usage < 70%** (ClickHouse + logs)

### Monitoring

```bash
# Günlük rapor
curl -s http://localhost:8080/analytics/daily_summary | jq

# Equity curve (son 24 saat)
curl -s http://localhost:8080/analytics/equity?hours=24 | jq

# Signal performance
curl -s http://localhost:8080/signals/performance?hours=24 | jq
```

---

## 🔐 Güvenlik Minimum Set

### Production Checklist

- [ ] `.env` dosyası Docker secrets / KMS'e taşındı
- [ ] Mini App initData HMAC verify aktif
- [ ] Config checksum monitoring aktif
- [ ] Telegram alert'leri çalışıyor
- [ ] Audit log retention 90 gün
- [ ] Backup stratejisi tanımlı

### Backup Commands

```bash
# ClickHouse backup
docker exec -it $(docker ps -qf name=clickhouse) clickhouse-client -q \
  "BACKUP DATABASE levibot TO Disk('backups', 'backup-$(date +%Y%m%d-%H%M%S).zip')"

# Redis AOF backup
docker cp $(docker ps -qf name=redis):/data/appendonly.aof \
  ./backups/redis-$(date +%Y%m%d-%H%M%S).aof

# Otomatik backup (cron)
# 0 2 * * * cd /opt/levibot && make backup
```

---

## 🧪 Parametre Tuning (Paper Mode)

### Signal Threshold

```bash
# Başlangıç: 0.58
# Test: 0.54, 0.55, 0.56, 0.57
# Hedef: En yüksek Sharpe ratio
MIN_CONFIDENCE=0.55
```

### Cooldown Period

```bash
# Başlangıç: 10 dakika
# Test: 5, 7, 8, 10 dakika
# Hedef: Overtrading'i önle, fırsatları kaçırma
COOLDOWN_MINUTES=7
```

### Position Sizing

```bash
# Başlangıç: 0.003 (0.3% risk per trade)
# Test: 0.002, 0.0025, 0.003
# Hedef: Max drawdown < 3%
PER_TRADE_RISK=0.0025
```

### Kelly Fraction

```bash
# Başlangıç: 0.25 (25% Kelly)
# Test: 0.15, 0.20, 0.25
# Hedef: Win rate'e göre optimize et
# Kelly = (win_rate * avg_win - (1-win_rate) * avg_loss) / avg_win
```

---

## 🎯 Sonraki Sprint Seçenekleri

### A) 7 Günlük Paper Raporu

- Otomatik PDF rapor oluşturma
- ClickHouse SQL analytics
- Performance breakdown (symbol, strategy, timeframe)
- Risk metrics (Sharpe, Sortino, Max DD, Calmar)
- Trade distribution analysis

### B) CI/CD Pipeline

- Staging environment setup
- Auto-deploy on merge to main
- Canary deployment strategy
- Rollback mechanism
- Health check gates

### C) SaaS Katmanı

- Multi-tenant architecture
- User authentication & authorization
- Config isolation per user
- Billing integration (Stripe/Iyzico)
- Usage tracking & limits

---

## 📞 Destek & Troubleshooting

### Log Locations

```bash
# Application logs
docker compose -f docker-compose.enterprise.yml logs [service_name]

# ClickHouse logs
docker exec -it $(docker ps -qf name=clickhouse) cat /var/log/clickhouse-server/clickhouse-server.log

# Redis logs
docker logs $(docker ps -qf name=redis)
```

### Debug Mode

```bash
# Enable debug logging
# .env içinde:
LOG_LEVEL=DEBUG

# Restart services
make restart
```

### Health Endpoints

```bash
# Panel API
curl http://localhost:8080/healthz

# Signal Engine
curl http://localhost:9100/metrics

# Executor
curl http://localhost:9101/metrics

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health
```

---

<p align="center">
  <strong>🚀 Preflight Complete - Ready for Takeoff! 🚀</strong><br>
  <em>Hayırlı uçuşlar paşam! 48 saatlik canary başlasın! 🔥</em>
</p>

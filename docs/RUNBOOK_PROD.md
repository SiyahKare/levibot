# LEVIBOT Production Runbook 🚀

Bu dokümant LEVIBOT'un prod ortamına deploy ve operasyonel yönetimi için adım adım kılavuzdur.

## İçindekiler

- [Canary Rollout](#canary-rollout)
- [Prod'a Terfi](#proda-terfi)
- [Emergency Kill Switch](#emergency-kill-switch)
- [Rollback Prosedürü](#rollback-prosedürü)
- [Monitoring & Alarmlar](#monitoring--alarmlar)
- [Günlük Operasyonlar](#günlük-operasyonlar)

---

## Canary Rollout

Canary mode, yeni değişiklikleri küçük bir sembol setiyle test etmek için kullanılır.

### 1. Canary Mode'u Aktifleştir

```bash
# API endpoint üzerinden
curl -X POST http://localhost:8000/admin/canary/on

# Response
{
  "ok": true,
  "canary_mode": true,
  "allow_symbols": ["BTCUSDT", "ETHUSDT"]
}
```

**Ne olur:**

- Sadece `configs/flags.yaml` içinde tanımlı `allow_symbols` için işlem yapılır
- Diğer semboller atlanır
- Log'larda `[CANARY]` etiketi görünür

### 2. Canary İzleme (15-30 dakika)

```bash
# Grafana dashboard'u kontrol et
http://localhost:3000/d/levibot-realtime

# Metrikleri izle
watch -n 5 'curl -s http://localhost:8000/paper/summary | jq ".stats"'

# Log'ları takip et
docker compose logs -f api | grep -i canary
```

**Kontrol Listesi:**

- [ ] Pozisyonlar sadece allow_symbols'da açılıyor mu?
- [ ] Latency normal mi? (<100ms p95)
- [ ] Error rate yükseldi mi?
- [ ] PnL beklendiği gibi mi?

### 3. Sorun Tespit Edilirse

```bash
# Canary'yi kapat
curl -X POST http://localhost:8000/admin/canary/off

# Veya acil durumda kill switch
curl -X POST http://localhost:8000/admin/kill
```

---

## Prod'a Terfi

Canary başarılı olduktan sonra tüm sembollere açılır.

### 1. Canary Mode'u Kapat

```bash
curl -X POST http://localhost:8000/admin/canary/off

# Response
{
  "ok": true,
  "canary_mode": false
}
```

**Ne olur:**

- Tüm semboller için işlem aktif olur
- Normal prod mod başlar

### 2. İlk 1 Saat İzleme

```bash
# Canlı PnL takibi
watch -n 10 'curl -s http://localhost:8000/paper/portfolio | jq ".total_pnl"'

# Prometheus alert kontrolü
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# Position count
curl -s http://localhost:8000/paper/positions | jq '.count'
```

**Kritik Metrikler:**

- Daily PnL > `max_daily_loss` (-200 USD)
- Open positions < `max_open_positions` (5)
- Win rate > 45%
- Error rate < 1%

---

## Emergency Kill Switch

Kritik bir sorun tespit edildiğinde tüm işlemleri anında durdurur.

### Aktifleştirme

```bash
curl -X POST http://localhost:8000/admin/kill

# Response
{
  "ok": true,
  "killed": true,
  "message": "Emergency kill switch activated. All trading stopped."
}
```

**Ne olur:**

- Tüm yeni işlemler engellenir
- Açık pozisyonlar açık kalır (manuel kapatılmalı)
- Trading engine'ler flag'i okur ve submit yapmaz

### Mevcut Pozisyonları Kapatma

```bash
# Tüm pozisyonları listele
curl http://localhost:8000/paper/positions | jq '.positions'

# Her pozisyonu manuel kapat
curl -X POST http://localhost:8000/paper/order \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "side": "sell", "notional_usd": 0}'
```

### Kill Switch'i Sıfırlama

```bash
# Sorun çözüldükten sonra
curl -X POST http://localhost:8000/admin/unkill

# Response
{
  "ok": true,
  "killed": false,
  "message": "Kill switch deactivated. Trading can resume."
}
```

---

## Rollback Prosedürü

Bir deployment'ta kritik bug bulunursa önceki versiyona dönülür.

### 1. Docker Image Rollback

```bash
# Mevcut image'i tag'le
docker tag levibot-api:latest levibot-api:rollback-backup

# Önceki stable tag'e geri dön (örnek: v1.5.0)
docker pull levibot-api:v1.5.0
docker tag levibot-api:v1.5.0 levibot-api:latest

# Container'ı yeniden başlat
docker compose down api
docker compose up -d api
```

### 2. Config Rollback

```bash
# Git'ten önceki flags.yaml'ı geri yükle
git checkout HEAD~1 configs/flags.yaml

# Veya manuel backup'tan
cp configs/flags.yaml.backup configs/flags.yaml

# Container'ı reload et (config hot-reload varsa gerek yok)
docker compose restart api
```

### 3. Database Rollback (gerekirse)

```bash
# Backup'tan restore
pg_restore -d levibot backup_YYYYMMDD.sql

# Veya TimescaleDB continuous aggregate'leri refresh et
psql -d levibot -c "CALL refresh_continuous_aggregate('market_1h', NULL, NULL);"
```

### 4. Doğrulama

```bash
# Sağlık kontrolü
make postfix-check

# Version kontrolü
curl http://localhost:8000/health | jq '.version'

# Log'larda hata var mı?
docker compose logs api --tail=50 | grep -i error
```

---

## Monitoring & Alarmlar

### Prometheus Alarmları

Kritik metrikler için tanımlı alarmlar:

1. **SSENoTicks** - SSE tick akışı durdu (1 dakika)
2. **TradingErrorsSpike** - Trading hata artışı (5 dakika içinde >0)
3. **DailyLossNearLimit** - Günlük zarar limite yaklaştı (-180 USD)
4. **EngineLatencyHigh** - Engine p95 latency >250ms (3 dakika)

### Alarm Kontrolü

```bash
# Firing alarmları listele
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing") | {alert: .labels.alertname, severity: .labels.severity}'

# Grafana alarm paneli
http://localhost:3000/alerting/list
```

### Manuel Metric Kontrolü

```bash
# SSE tick rate
curl -s http://localhost:8000/metrics | grep 'levibot_latency_ms_count{stage="ticks"}'

# Error rate
curl -s http://localhost:8000/metrics | grep 'levibot_errors_total'

# Equity
curl -s http://localhost:8000/metrics | grep 'levibot_equity'
```

---

## Günlük Operasyonlar

### Sabah Kontrolleri (09:00)

```bash
# 1. Nightly replay sonuçları
cat backend/data/reports/replay_$(date +%Y%m%d).json

# 2. Gece PnL özeti
curl http://localhost:8000/paper/performance | jq '.total_return_pct'

# 3. Alarm history
curl http://localhost:9090/api/v1/query?query=ALERTS | jq '.data.result'

# 4. Position health
curl http://localhost:8000/paper/positions | jq '.positions[] | select(.pnl_usd < -50)'
```

### Akşam Kapanış (18:00)

```bash
# 1. Daily PnL raporu
curl http://localhost:8000/paper/summary | jq '{equity: .stats.total_equity, pnl: .stats.total_pnl, trades: .stats.total_trades, win_rate: .stats.win_rate}'

# 2. Backup oluştur
pg_dump levibot > backup_$(date +%Y%m%d).sql

# 3. Flags durumunu kaydet
cp configs/flags.yaml configs/flags.yaml.$(date +%Y%m%d)

# 4. Log rotation
docker compose logs api > logs/api_$(date +%Y%m%d).log
```

---

## Runtime Flag Yönetimi

### Flag'leri Görüntüleme

```bash
curl http://localhost:8000/admin/flags | jq '.flags'
```

### Flag Değiştirme

```bash
# Max daily loss limitini değiştir
curl -X POST "http://localhost:8000/admin/set-flag?key=max_daily_loss&value=-300.0"

# Telegram alert'leri kapat
curl -X POST "http://localhost:8000/admin/set-flag?key=enable_telegram_alerts&value=false"

# Max position size artır
curl -X POST "http://localhost:8000/admin/set-flag?key=max_position_size_usd&value=2000.0"
```

---

## Troubleshooting

### Problem: Pozisyonlar açılmıyor

```bash
# 1. Kill switch aktif mi?
curl http://localhost:8000/admin/flags | jq '.flags.killed'

# 2. Canary mode aktif mi ve sembol izinli mi?
curl http://localhost:8000/admin/health

# 3. Balance yeterli mi?
curl http://localhost:8000/paper/portfolio | jq '.cash_balance'

# 4. Daily loss limitine ulaşıldı mı?
curl http://localhost:8000/paper/portfolio | jq '.total_pnl'
```

### Problem: Latency yüksek

```bash
# 1. Prometheus'ta p95 latency kontrol et
curl http://localhost:8000/metrics | grep levibot_latency_ms

# 2. SSE event queue doldu mu?
docker compose logs api | grep "queue.*full"

# 3. DB connection pool durumu
docker compose logs api | grep "pool"

# 4. Redis memory
docker compose exec redis redis-cli INFO memory | grep used_memory_human
```

### Problem: PnL beklenenden farklı

```bash
# 1. Paper portfolio stats
curl http://localhost:8000/paper/summary | jq

# 2. Son 10 trade'i incele
curl http://localhost:8000/paper/trades?limit=10 | jq '.trades'

# 3. Open positions unrealized PnL
curl http://localhost:8000/paper/positions | jq '[.positions[].pnl_usd] | add'

# 4. Replay ile karşılaştır
python scripts/replay_24h.py
```

---

## İletişim & Escalation

### Severity Levels

- **P0 (Critical)**: Kill switch aktif, sistem down
  - Action: Immediate rollback + notify team
- **P1 (High)**: Daily loss limit aşıldı, çok sayıda hata
  - Action: Enable canary mode + investigate
- **P2 (Medium)**: Latency yüksek, bazı semboller fail
  - Action: Monitor + schedule fix
- **P3 (Low)**: Minor bugs, UI issues
  - Action: Log + fix next sprint

---

## Checklist: Pre-Deployment

Prod'a deploy öncesi kontroller:

- [ ] `make postfix-check` tüm testler geçiyor
- [ ] Canary mode test edildi (15+ dakika)
- [ ] Prometheus alarmları configured
- [ ] Grafana dashboard erişilebilir
- [ ] Backup alındı (DB + configs)
- [ ] Rollback plan hazır
- [ ] Team bilgilendirildi
- [ ] Kill switch testi yapıldı
- [ ] Log rotation configured
- [ ] Nightly replay job çalışıyor

---

## Checklist: Post-Deployment

Deploy sonrası ilk 24 saat:

- [ ] İlk 1 saat: 5 dakikada bir metrik kontrolü
- [ ] İlk 6 saat: Her saat PnL raporu
- [ ] İlk 24 saat: Her 4 saatte alarm kontrolü
- [ ] Nightly replay sonucu incelendi
- [ ] Daily PnL limit içinde
- [ ] Hiçbir firing alarm yok
- [ ] Error rate < 1%
- [ ] Latency p95 < 150ms

---

## Kaynaklar

- **Grafana Dashboard**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **API Docs**: http://localhost:8000/docs
- **Panel**: http://localhost:3001

**🚨 Acil durumda: `curl -X POST http://localhost:8000/admin/kill`**

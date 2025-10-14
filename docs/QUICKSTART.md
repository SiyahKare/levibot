# 🚀 LeviBot Enterprise - Hızlı Başlangıç

> **Enterprise-grade AI Signals Platform** - 5 dakikada ayağa kaldır!

---

## ⚡ Tek Komutla Başlat

```bash
# 1. Environment dosyasını kopyala
cp ENV.levibot.example .env

# 2. .env dosyasını düzenle (önemli alanlar)
nano .env

# 3. Sistemi başlat
make up

# 4. Logları izle
make logs
```

---

## 📋 Gerekli Konfigürasyonlar

### `.env` Dosyasında Mutlaka Değiştir:

```bash
# Telegram Bot Token (BotFather'dan al)
TG_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi

# Telegram Admin Chat ID (userinfobot'tan öğren)
TG_ADMIN_CHAT_ID=123456789

# API Security (32+ karakter güçlü key)
API_AUTH_SECRET=your_super_secure_hmac_key_min_32_characters

# Exchange Credentials (MEXC)
MEXC_API_KEY=your_mexc_api_key
MEXC_SECRET=your_mexc_secret
```

### Telegram Bot Token Nasıl Alınır?

1. Telegram'da [@BotFather](https://t.me/BotFather) ara
2. `/newbot` komutunu gönder
3. Bot adını belirle (örn: "LeviBot Signals")
4. Username belirle (örn: "levibot_signals_bot")
5. Token'ı kopyala ve `.env` dosyasına yapıştır

### Chat ID Nasıl Öğrenilir?

1. Telegram'da [@userinfobot](https://t.me/userinfobot) ara
2. `/start` komutunu gönder
3. "Id" numarasını kopyala ve `.env` dosyasına yapıştır

---

## 🎯 Sistem Kontrolü

### Servis Durumunu Kontrol Et

```bash
make ps
```

**Beklenen Çıktı:**

```
NAME                      STATUS              PORTS
levibot-panel             Up (healthy)        0.0.0.0:8080->8080/tcp
levibot-signal-engine     Up                  0.0.0.0:9100->9100/tcp
levibot-executor          Up                  0.0.0.0:9101->9101/tcp
levibot-telegram-bot      Up
levibot-miniapp           Up                  0.0.0.0:5173->5173/tcp
levibot-redis             Up (healthy)        0.0.0.0:6379->6379/tcp
levibot-clickhouse        Up (healthy)        0.0.0.0:8123->8123/tcp
levibot-prometheus        Up                  0.0.0.0:9090->9090/tcp
levibot-grafana           Up                  0.0.0.0:3000->3000/tcp
```

### Smoke Test Çalıştır

```bash
make smoke-test
```

**Beklenen Çıktı:**

```
✓ Panel API healthy
✓ Redis healthy
✓ ClickHouse healthy
✓ Prometheus healthy
✓ Grafana healthy
```

---

## 🎮 Kullanım

### Telegram Bot'u Kullan

1. Telegram'da botunu ara (örn: @levibot_signals_bot)
2. `/start` komutunu gönder
3. Mini App panelini aç
4. Canlı PnL, sinyal geçmişi ve kontrolleri gör

### Grafana Dashboard'ları Aç

```bash
make monitor
```

- **Grafana:** http://localhost:3000 (admin/admin)
- **Prometheus:** http://localhost:9090
- **Panel API:** http://localhost:8080

### Logları İzle

```bash
# Tüm servisler
make logs

# Sadece Signal Engine
make logs-signal

# Sadece Executor
make logs-executor

# Sadece Telegram Bot
make logs-bot
```

---

## 🔧 Yararlı Komutlar

```bash
# Servisleri yeniden başlat
make restart

# Servisleri durdur
make down

# Veritabanını başlat
make init-db

# Docker istatistiklerini göster
make stats

# Redis CLI aç
make shell-redis

# ClickHouse CLI aç
make shell-clickhouse

# Panel container'ına shell aç
make shell-panel

# Backup al
make backup

# Tüm verileri temizle (DİKKAT!)
make clean
```

---

## 📊 İlk Sinyalleri Görmek

### 1. Sistem Ayağa Kalktıktan Sonra

Signal Engine otomatik olarak:

- OHLCV verilerini çekmeye başlar
- Feature'ları hesaplar
- ML modeli ile tahmin yapar
- Policy Engine'den geçirir
- Uygun sinyalleri yayınlar

### 2. Telegram'dan Kontrol Et

```
/status
```

**Örnek Çıktı:**

```
📊 LeviBot Status

💰 Equity: $10,000.00
📈 Daily PnL: +$125.50 (+1.26%)
🎯 Daily Trades: 3/50
⏰ Last Trade: 5m ago
🔒 Kill Switch: OFF

✅ All systems operational
```

### 3. Grafana'da İzle

- **Equity Curve:** Gerçek zamanlı sermaye grafiği
- **Signal Performance:** Sinyal başarı oranları
- **System Health:** Latency, throughput, error rates

---

## 🐛 Sorun Giderme

### Servis Ayağa Kalkmıyor

```bash
# Logları kontrol et
docker compose -f docker-compose.enterprise.yml logs [service_name]

# Örnek: Panel loglarını kontrol et
docker compose -f docker-compose.enterprise.yml logs panel
```

### Redis Bağlantı Hatası

```bash
# Redis'in çalıştığını kontrol et
docker compose -f docker-compose.enterprise.yml ps redis

# Redis'i yeniden başlat
docker compose -f docker-compose.enterprise.yml restart redis
```

### ClickHouse Bağlantı Hatası

```bash
# ClickHouse'un çalıştığını kontrol et
curl http://localhost:8123/ping

# ClickHouse'u yeniden başlat
docker compose -f docker-compose.enterprise.yml restart clickhouse

# Veritabanını yeniden başlat
make init-db
```

### Telegram Bot Yanıt Vermiyor

```bash
# Bot loglarını kontrol et
make logs-bot

# .env dosyasında TG_BOT_TOKEN'ı kontrol et
grep TG_BOT_TOKEN .env

# Bot'u yeniden başlat
docker compose -f docker-compose.enterprise.yml restart telegram_bot
```

---

## 🔐 Güvenlik Notları

1. **`.env` dosyasını asla commit etme!**
2. **API_AUTH_SECRET** en az 32 karakter olmalı
3. **Production'da Grafana şifresini değiştir**
4. **Binance API key'lerine sadece testnet izinleri ver**
5. **Telegram bot'u sadece admin chat ID'sine yanıt verir**

---

## 📚 Daha Fazla Bilgi

- **Detaylı Deployment:** [DEPLOYMENT_GUIDE.md](./docs/DEPLOYMENT_GUIDE.md)
- **Mimari:** [ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- **ML Pipeline:** [ML_SPRINT3_GUIDE.md](./docs/ML_SPRINT3_GUIDE.md)
- **Production Runbook:** [RUNBOOK_PROD.md](./RUNBOOK_PROD.md)

---

## 🎉 Başarılı Kurulum Sonrası

Sistem çalışıyorsa:

1. ✅ Telegram bot'undan `/start` ile panel aç
2. ✅ Grafana'da equity curve'ü izle
3. ✅ 24-48 saat paper trading'i gözlemle
4. ✅ Metrikleri analiz et
5. ✅ Production'a geçmeye hazır!

---

**🚀 Hayırlı işler paşam! LeviBot artık enterprise-grade!**

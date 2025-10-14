# Multi-Symbol Universe System 🌍

**LeviBot'un 20-30 coinlik evreninde optimize edilmiş çoklu sembol trading sistemi.**

---

## 📊 Özet

Bu sistem, LeviBot'un **tek bir sembol yerine 20-30 coin'lik bir evren** üzerinde çalışmasını sağlar. MEXC'den real-time veri alır, anomalileri filtreler ve LSE/Day/Swing motorlarını optimize eder.

**Durum:** ✅ **TAMAMLANDI (18/18 TODO)**

---

## 🎯 Özellikler

### 1️⃣ **Universe Yönetimi**

- **Core Symbols (10):** BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, DOGEUSDT, TONUSDT, TRXUSDT, AVAXUSDT, LINKUSDT
- **Tier 2 Symbols (14):** ADAUSDT, MATICUSDT, DOTUSDT, NEARUSDT, ATOMUSDT, ARBUSDT, OPUSDT, APTUSDT, SUIUSDT, INJUSDT, IMXUSDT, AAVEUSDT, UNIUSDT, RUNEUSDT
- **Rotasyon:** 15 dakikada bir, volatilite + hacim bazlı
- **Config:** `configs/universe.yaml`

### 2️⃣ **MEXC Feed Entegrasyonu**

- **WebSocket:** `wss://wbs.mexc.com/raw`
- **Topics:** `deals` (trades) + `book_ticker` (best bid/ask)
- **Outlier Filter:** ±10% median band dışındaki tick'leri filtreler
- **Batch Insert:** 1000 row/flush ile performans optimizasyonu
- **Config:** `configs/feed.yaml`

### 3️⃣ **Price Guards**

- **Median Check:** Son 5 dakika median'ından ±10% dışındaki fiyatları reddeder
- **Min/Max Clamp:** Symbol-specific limitler (örn. BTCUSDT: $10k-$150k)
- **Entry Guard:** Trade entry'den önce fiyat anomalisi kontrolü
- **Backend:** `backend/src/strategies/lse/price_guards.py`

### 4️⃣ **Multi-Symbol Support**

- **Symbol Parameter:** `/lse/health?symbol=BTCUSDT`
- **Batch Run:** `/lse/run_batch` endpoint (çoklu sembol start/stop)
- **Per-Symbol Config:** `overrides.symbol` ile runtime override

### 5️⃣ **UI Enhancement**

- **Watchlist Page:** 24 sembol grid (Core + Tier 2)
- **Symbol Dropdown:** Scalp sayfasında sembol seçimi
- **Quick Select:** Top-vol coinler için hızlı seçim butonları
- **Price Anomaly Warning:** >5% deviation için görsel uyarı

---

## 🚀 Hızlı Başlangıç

### 1. **Feed Teşhis**

```bash
make feed-diagnose
```

**Çıktı:**

- Son 20 tick (fiyat, bid, ask, spread, latency)
- 24h fiyat istatistikleri (min, max, median, std)
- Anomali kontrolü (±50% bandı)
- Son 10 trade

### 2. **Anormal Tick Temizleme**

```bash
# Dry-run (sadece kontrol)
make feed-clean

# Execute (gerçekten temizle)
make feed-clean-execute
```

**Ne Yapar:**

- 24h median hesaplar
- ±2x median dışındaki tick'leri siler
- Her sembol için ayrı ayrı işler

### 3. **Universe Kontrolü**

```bash
make universe-list
```

**Çıktı:**

```json
{
  "ok": true,
  "symbols": ["BTCUSDT", "ETHUSDT", ...],
  "core": ["BTCUSDT", "ETHUSDT", ...],
  "tier2_active": ["ADAUSDT", "MATICUSDT", ...],
  "total": 24
}
```

### 4. **LSE Health Check**

```bash
make lse-health

# veya
curl http://localhost:8000/lse/health?symbol=BTCUSDT | jq
```

---

## 📡 API Endpoints

### Universe

| Endpoint             | Method | Açıklama                |
| -------------------- | ------ | ----------------------- |
| `/universe/active`   | GET    | Aktif semboller         |
| `/universe/config`   | GET    | Tam config              |
| `/universe/override` | POST   | Manuel override (admin) |
| `/universe/metrics`  | GET    | Sembol bazlı metrikler  |

### Feed

| Endpoint              | Method | Açıklama                |
| --------------------- | ------ | ----------------------- |
| `/feed/health`        | GET    | WS sağlık kontrolü      |
| `/feed/metrics`       | GET    | Sembol bazlı metrikler  |
| `/feed/reconnect`     | POST   | Force reconnect (admin) |
| `/feed/subscriptions` | GET    | Aktif subscription'lar  |

### LSE (Multi-Symbol)

| Endpoint                     | Method | Açıklama                     |
| ---------------------------- | ------ | ---------------------------- |
| `/lse/health?symbol=BTCUSDT` | GET    | Sembol bazlı health          |
| `/lse/run`                   | POST   | Start/stop (symbol override) |
| `/lse/run_batch`             | POST   | Çoklu sembol start/stop      |

---

## 🎨 Frontend Sayfaları

### Watchlist (`/watchlist`)

- **24 sembol grid** (Core + Tier 2)
- **Live status** (running/idle)
- **Metrics:** Price, Vol 1h, Spread
- **Quick Trade:** Her sembol için "Trade" butonu

### Scalp (`/scalp`)

- **Symbol Dropdown:** Tüm aktif semboller
- **Quick Select:** Top-6 core coinler
- **Price Anomaly Warning:** >5% deviation için uyarı
- **Engine Status:** WS, guards, running, mode, position
- **PnL Sparkline:** 24h equity curve
- **Recent Trades:** DB'den real-time

---

## 🛡️ Güvenlik & Performans

### Price Guards

```python
# backend/src/strategies/lse/price_guards.py
guard = PriceGuard(symbol="BTCUSDT")
guard.update(price)

is_ok, reason = guard.check_price(price)
if not is_ok:
    # Block trade
    print(f"⚠️ Price anomaly: {reason}")
```

**Guard Tipi:**

1. **Clamp Check:** Min/max band (symbol-specific)
2. **Median Check:** ±10% 5dk median
3. **Rate Limit:** Hızlı fiyat değişimi

### Feed Outlier Filter

```yaml
# configs/feed.yaml
processing:
  outlier_filter:
    enabled: true
    method: median_band
    window_sec: 300 # 5 minutes
    threshold_pct: 10 # ±10%
```

**Ne Yapar:**

- Son 5 dakika median hesaplar
- ±10% dışındaki tick'leri **DB'ye yazmaz**
- Gerçek zamanlı filtreleme

---

## 📈 Metrikler & İzleme

### Feed Metrics

- **Recv Rate:** Msg/sec
- **Tick Rate:** Tick/sec (dedup sonrası)
- **Latency:** p50, p95, p99
- **Outliers:** 1 dakikada filtrelen tick sayısı

### Universe Metrics

- **Vol 1h:** 1 saatlik realized volatilite
- **Volume 24h:** 24 saatlik hacim
- **Spread:** Best bid/ask spread (bps)
- **Trades/min:** Dakikadaki trade sayısı

---

## 🔧 Config Dosyaları

### `configs/universe.yaml`

```yaml
universe:
  core: [BTCUSDT, ETHUSDT, ...]
  tier2: [ADAUSDT, MATICUSDT, ...]
  max_active: 24
  rotation:
    enabled: true
    interval_sec: 900
    min_trades_per_min: 10
    min_24h_vol_usd: 2000000
```

### `configs/feed.yaml`

```yaml
feed:
  provider: mexc
  websocket:
    url: wss://wbs.mexc.com/raw
    heartbeat_sec: 25
  topics:
    deals: true
    book_ticker: true
  processing:
    outlier_filter:
      enabled: true
      threshold_pct: 10
```

### `configs/lse.prod.yaml`

```yaml
# Price source sabitleme
price_source: ws_mid
prefer_ws_price: true

# Price guards
price_guards:
  enabled: true
  median_check:
    window_sec: 300
    threshold_pct: 10
  clamps:
    min_price: 10000
    max_price: 150000
```

---

## 📝 Makefile Komutları

### Feed

```bash
make feed-diagnose       # Feed teşhis
make feed-clean          # Anormal tick temizle (dry-run)
make feed-clean-execute  # Gerçekten temizle
```

### Universe

```bash
make universe-list       # Aktif semboller
```

### LSE

```bash
make lse-health          # Health check
make lse-smoke           # Smoke test
```

### Docker

```bash
make docker-up           # Start all
make docker-down         # Stop all
make docker-restart      # Restart all
make docker-logs         # Show logs
```

---

## 🎯 Sonraki Adımlar

1. **Feed Kurulumu**

   ```bash
   make feed-diagnose
   make feed-clean-execute
   docker compose restart api
   ```

2. **UI Test**

   - http://localhost:3002/watchlist
   - http://localhost:3002/scalp

3. **Multi-Symbol Test**

   ```bash
   curl -X POST http://localhost:8000/lse/run_batch \
     -H 'Content-Type: application/json' \
     -d '{"symbols":["BTCUSDT","ETHUSDT"],"action":"start","mode":"paper"}'
   ```

4. **Monitoring**
   ```bash
   watch -n 5 'curl -s http://localhost:8000/feed/health | jq'
   watch -n 5 'curl -s http://localhost:8000/universe/active | jq .total'
   ```

---

## 🐛 Troubleshooting

### Feed bağlanmıyor

```bash
# WS status kontrol
curl http://localhost:8000/feed/health | jq .ws_connected

# Manuel reconnect
curl -X POST http://localhost:8000/feed/reconnect
```

### Anormal fiyatlar

```bash
# Teşhis
make feed-diagnose

# Temizlik
make feed-clean-execute

# Guard'lar kontrol
curl http://localhost:8000/lse/health?symbol=BTCUSDT | jq .guards
```

### Universe boş

```bash
# Config kontrol
cat configs/universe.yaml

# API restart
docker compose restart api

# Tekrar kontrol
make universe-list
```

---

## 📚 İlgili Dökümanlar

- [Universe Config](../configs/universe.yaml)
- [Feed Config](../configs/feed.yaml)
- [LSE Prod Config](../configs/lse.prod.yaml)
- [Price Guards](../backend/src/strategies/lse/price_guards.py)
- [Universe Routes](../backend/src/app/routes/universe.py)
- [Feed Routes](../backend/src/app/routes/feed.py)
- [Watchlist UI](../frontend/panel/src/pages/Watchlist.tsx)
- [Scalp UI (Updated)](../frontend/panel/src/pages/Scalp.tsx)

---

**Durum:** ✅ Production Ready  
**Son Güncelleme:** 2025-10-11  
**Versiyon:** v1.0.0

💙 **LeviBot Multi-Symbol Universe is LIVE!** 🚀


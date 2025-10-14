# Grafana Dashboards for LEVIBOT

Bu dizin LEVIBOT realtime operations için Grafana dashboard'larını içerir.

## Dashboard'lar

### 1. Realtime Operations (`realtime_ops.json`)

Prod operasyonları için ana dashboard. İçerik:

**Üst Panel (Metrics Overview):**

- Portfolio Equity (anlık değer)
- Open Positions (pozisyon sayısı)
- Daily PnL (günlük kar/zarar)
- Win Rate (kazanma oranı %)
- System Status (UP/DOWN)

**Orta Panel (Charts):**

- Equity Curve (son 1 saat)
- SSE Event Rate (tick ve signal/dk)
- Engine Latency (p50, p95, p99)
- Error Rate (modül bazında)

**Alt Panel (Details):**

- Recent Positions (tablo)
- Recent Alerts (log stream)
- HTTP Status Codes (5dk bar chart)
- Canary Mode & Kill Switch status
- Redis/DB Connections

**Annotations:**

- Deployments (version tags)
- Alerts (firing alarms)

---

## Kurulum

### Otomatik Yükleme (Docker Compose)

Dashboard'lar otomatik olarak yüklenir:

```bash
# Docker compose'u başlat
docker compose up -d

# Grafana'ya eriş
open http://localhost:3000

# Default credentials: admin / admin
```

### Manuel Import

1. Grafana UI'a gir: `http://localhost:3000`
2. Sol menüden **Dashboards** → **Import**
3. **Upload JSON file** butonuna tıkla
4. `ops/grafana/dashboards/realtime_ops.json` seç
5. **Prometheus** datasource'u seç
6. **Import** butonuna tıkla

---

## Dashboard Kullanımı

### Canary Rollout İzleme

1. Dashboard'u aç
2. Sağ üstten **Refresh interval: 5s** ayarla
3. **Canary Mode** panel'ine bak (sarı = ON)
4. İlk 15 dakika:
   - Equity Curve düzgün yükseliyor mu?
   - Error Rate sıfır mı?
   - Latency p95 < 150ms mi?
5. Sorun yoksa `/admin/canary/off` ile prod'a terfi et

### Alert Takibi

**Firing Alerts** (annotations):

- Dashboard üstünde kırmızı dikey çizgiler
- Üzerine gel → alert detayları görünür

**Recent Alerts** (log panel):

- Son 1 saatin ALERT/ERROR/CRITICAL logları
- Click → tam log metni

### Kill Switch Kontrolü

**Kill Switch panel'i:**

- **YEŞIL (ACTIVE)**: Normal trading
- **KIRMIZI (KILLED)**: Tüm işlemler durdu

Acil durumda:

```bash
curl -X POST http://localhost:8000/admin/kill
```

---

## Prometheus Metrics Referansı

Dashboard'un kullandığı ana metrikler:

| Metric                        | Açıklama                 | Birim   |
| ----------------------------- | ------------------------ | ------- |
| `levibot_equity`              | Portfolio equity         | USD     |
| `levibot_open_positions`      | Açık pozisyon sayısı     | count   |
| `levibot_drawdown`            | Günlük PnL               | USD     |
| `levibot_win_rate`            | Kazanan trade %          | percent |
| `levibot_latency_ms_bucket`   | Engine latency histogram | ms      |
| `levibot_errors_total`        | Toplam hata sayısı       | count   |
| `levibot_http_requests_total` | HTTP istek sayısı        | count   |
| `levibot_canary_mode`         | Canary mode durumu       | 0/1     |
| `levibot_killed`              | Kill switch durumu       | 0/1     |

Detaylı liste için: `curl http://localhost:8000/metrics`

---

## Troubleshooting

### Dashboard yüklenmiyor

```bash
# Grafana container'ını kontrol et
docker compose logs grafana | tail -50

# Provisioning klasörünü kontrol et
docker compose exec grafana ls -la /var/lib/grafana/dashboards

# Dashboard'u manuel import et (yukarıdaki adımlar)
```

### Metrikler görünmüyor

```bash
# Prometheus'u kontrol et
curl http://localhost:9090/api/v1/query?query=up

# API metrics endpoint'i kontrol et
curl http://localhost:8000/metrics

# Prometheus targets
open http://localhost:9090/targets
```

### Panel "No data" gösteriyor

- **Zaman aralığını kontrol et**: Sağ üst köşeden "Last 1 hour" seç
- **Prometheus datasource'u kontrol et**: Settings → Data sources → Prometheus
- **Metric adını doğrula**: Panel edit → Metrics browser

---

## Özelleştirme

### Panel Ekleme

1. Dashboard'u aç
2. Sağ üst **Add panel** → **Add a new panel**
3. Query'i yaz (örn: `rate(levibot_errors_total[5m])`)
4. Visualization type seç (Graph, Stat, Table, vb.)
5. **Apply** → **Save dashboard**

### Alert Ekleme

1. Panel edit moduna gir
2. **Alert** tab'ına tıkla
3. **Create alert rule**
4. Conditions ekle (örn: `p95 latency > 250ms for 3m`)
5. Notification channel seç (Telegram, Slack, vb.)
6. **Save**

### Değişkenleri Kullanma

Zaten tanımlı:

- `$datasource` - Prometheus datasource

Yeni eklemek için:

1. Dashboard settings ⚙️
2. **Variables** → **Add variable**
3. Örnek: `symbol` variable (BTCUSDT, ETHUSDT, ...)
4. Query'lerde kullan: `levibot_equity{symbol=~"$symbol"}`

---

## Production Checklist

Deploy öncesi kontroller:

- [ ] Grafana `http://localhost:3000` erişilebilir
- [ ] Prometheus `http://localhost:9090` erişilebilir
- [ ] Dashboard import edildi
- [ ] Tüm paneller veri gösteriyor
- [ ] Alert rules configured (ops/prometheus/rules.yml)
- [ ] Notification channel configured (Telegram/Slack)
- [ ] Team'e dashboard linki paylaşıldı

---

## Kaynaklar

- [Grafana Docs](https://grafana.com/docs/)
- [Prometheus Query Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [LEVIBOT RUNBOOK](/RUNBOOK_PROD.md)

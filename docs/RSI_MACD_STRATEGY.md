# RSI + MACD Strategy 🎯

**Kombine momentum + trend stratejisi**

## 📊 Strateji Özeti

RSI + MACD stratejisi, **RSI'nın momentum sinyallerini** ve **MACD'nin trend konfirmasyonunu** birleştirerek yüksek olasılıklı giriş noktaları yakalar.

### Temel Mantık

1. **Trend Filtresi:** MACD histogramı sıfır çizgisini keser (pozitif = long bias, negatif = short bias)
2. **Momentum Tetik:** RSI 50 eşiğini kapanışla keser
3. **Senkronizasyon:** İki koşul aynı mumda veya N mum içinde (2-3 bar) gerçekleşmeli
4. **Guardlar:** Spread, latency, volatilite kontrolleri geçilmeli

### Çıkış Mantığı

- MACD histogram ters yöne döner
- RSI 50 eşiğini ters keser
- ATR bazlı SL/TP seviyelerine ulaşılır
- Timeout (max bar sayısı aşılır)

---

## ⚙️ Modlar ve Preset'ler

### 🚀 Scalp Mode (`1m`)

- **Hedef:** %55+ win rate, PF ≥ 1.15
- **R:R:** 1.2:1.2 (simetrik)
- **Timeout:** 30 bar (~30 dakika)
- **Cooldown:** 5 bar
- **Budget:** $150/trade

**Kullanım:**

```bash
curl -X POST http://localhost:8000/strategy/rsi-macd/load-preset?mode=scalp
curl -X POST http://localhost:8000/strategy/rsi-macd/run?action=start
```

### 📈 Day Mode (`15m`)

- **Hedef:** PF ≥ 1.25
- **R:R:** 1.5:2.0
- **Timeout:** 24 bar (~6 saat)
- **Cooldown:** 8 bar (~2 saat)
- **Budget:** $300/trade

**Kullanım:**

```bash
curl -X POST http://localhost:8000/strategy/rsi-macd/load-preset?mode=day
curl -X POST http://localhost:8000/strategy/rsi-macd/run?action=start
```

### 🌊 Swing Mode (`4h`)

- **Hedef:** PF ≥ 1.5, Calmar ≥ 0.5
- **R:R:** 2.0:3.0
- **Timeout:** 10 bar (~40 saat)
- **Cooldown:** 0 bar
- **Sizing:** %0.5 risk/trade
- **Partial TP:** 1R ve 2R'de %50 profit al

**Kullanım:**

```bash
curl -X POST http://localhost:8000/strategy/rsi-macd/load-preset?mode=swing
curl -X POST http://localhost:8000/strategy/rsi-macd/run?action=start
```

---

## 🖥️ Panel Kullanımı

### UI: `/rsi-macd`

**Özellikler:**

- ✅ Mod seçimi (Scalp/Day/Swing)
- ✅ Start/Stop kontrolleri
- ✅ Live features (RSI, MACD Hist, ATR, ADX)
- ✅ PnL özeti (total, win rate, trades)
- ✅ Recent trades tablosu

**Erişim:**

```
http://localhost:3002/rsi-macd
```

---

## 🧪 Test ve Backtest

### Smoke Test

```bash
make rsi-macd-smoke
```

### Backtest (30-90 gün)

```bash
# Scalp (30 gün)
make rsi-macd-backtest-scalp

# Day (60 gün)
make rsi-macd-backtest-day

# Swing (90 gün, equity curve plot dahil)
make rsi-macd-backtest-swing
```

### Manuel Backtest

```bash
cd backend
python scripts/backtest_rsi_macd.py --mode day --days 60 --report --plot
```

**Output:**

- `backend/data/backtests/rsi_macd_{mode}_{days}d_trades.csv`
- `backend/data/backtests/rsi_macd_{mode}_{days}d_equity.png` (eğer `--plot` kullanıldıysa)

---

## 📡 API Endpoints

### Health

```bash
curl http://localhost:8000/strategy/rsi-macd/health | jq
```

**Response:**

```json
{
  "running": true,
  "mode": "day",
  "symbol": "BTCUSDT",
  "tf": "15m",
  "position": "long",
  "features": {
    "rsi": 62.5,
    "macd_hist": 15.8,
    "macd_line": 120.5,
    "macd_signal": 104.7,
    "atr": 180.2,
    "adx": 28.5
  },
  "current_bar": 1543,
  "cooldown_active": false,
  "total_pnl": 125.5,
  "trades": 15,
  "win_rate": 60.0
}
```

### Get Parameters

```bash
curl http://localhost:8000/strategy/rsi-macd/params | jq
```

### Update Parameters

```bash
curl -X POST http://localhost:8000/strategy/rsi-macd/params \
  -H 'Content-Type: application/json' \
  -d '{"rsi.period": 21, "macd.fast": 10}'
```

### Start/Stop

```bash
# Start
curl -X POST http://localhost:8000/strategy/rsi-macd/run?action=start

# Stop
curl -X POST http://localhost:8000/strategy/rsi-macd/run?action=stop
```

### PnL Summary

```bash
curl http://localhost:8000/strategy/rsi-macd/pnl | jq
```

**Response:**

```json
{
  "total_pnl": 125.5,
  "num_trades": 15,
  "num_wins": 9,
  "num_losses": 6,
  "win_rate": 60.0,
  "profit_factor": 1.42
}
```

### Recent Trades

```bash
curl http://localhost:8000/strategy/rsi-macd/trades/recent?limit=20 | jq
```

---

## 🔧 Config Dosyaları

### Scalp

`configs/rsi_macd.scalp.yaml`

### Day

`configs/rsi_macd.day.yaml`

### Swing

`configs/rsi_macd.swing.yaml`

---

## 💡 Pratik İpuçları

### 1. Sync Window

- Scalp: ≤2 bar (sıkı senkronizasyon)
- Day: ≤3 bar
- Swing: ≤3 bar

**Neden?** Gecikmeli sinyaller gürültülü ve düşük kaliteli.

### 2. Fee Check

Her sinyal öncesi:

```
expected_edge > (fee + slippage)
```

Scalp için kritik! (7 bps fee + ~3 bps slippage = 10 bps total)

### 3. Cooldown

- Scalp: 5 bar (overtrading'i önler)
- Day: 8 bar (~2 saat)
- Swing: 0 bar (uzun TF'de gereksiz)

### 4. ADX Filtresi (Swing only)

- Min ADX: 18
- **Neden?** Swing sadece trendy piyasalarda çalışmalı

### 5. Partial TP (Swing only)

- 1R'de %50 al → risk sıfırla
- 2R'de kalan %50'yi al

---

## 🚀 Canlıya Alma (Production)

### 1. Backtest Doğrulama

```bash
make rsi-macd-backtest-day  # ≥60 gün
```

**Hedefler:**

- Win rate ≥ %55 (scalp)
- PF ≥ 1.25 (day)
- PF ≥ 1.5 (swing)

### 2. Paper Test (7-14 gün)

```bash
curl -X POST http://localhost:8000/strategy/rsi-macd/load-preset?mode=day
curl -X POST http://localhost:8000/strategy/rsi-macd/run?action=start
```

**Monitoring:**

```bash
watch -n 5 'curl -s http://localhost:8000/strategy/rsi-macd/health | jq'
```

### 3. Küçük Sermaye Test (7 gün)

- **Başlangıç:** $100-200 (day mode)
- **Max risk:** %0.5/trade
- **Günlük limit:** 3 trade

### 4. Ölçeklendirme

Eğer 7 gün PF ≥ 1.2 ise:

- Budget → 2x artır
- Daily limit → 5 trade

---

## 📊 Metrics

### Prometheus

```
# Feature staleness
ml_feature_staleness_seconds{feature="rsi"}
ml_feature_staleness_seconds{feature="macd"}

# Strategy PnL
strategy_pnl_total{strategy="rsi_macd", mode="day"}

# Trade count
strategy_trades_total{strategy="rsi_macd", outcome="win"}
strategy_trades_total{strategy="rsi_macd", outcome="loss"}
```

### Grafana Dashboard

```
Panel 1: RSI + MACD Hist (dual axis)
Panel 2: Equity Curve
Panel 3: Win Rate (rolling 20 trades)
Panel 4: PnL Distribution (histogram)
```

---

## ⚠️ Risk Uyarıları

### 1. Sideways Piyasalar

RSI+MACD **trend takip** stratejisi → range'de whipsaw riski yüksek!

**Çözüm:** ADX < 15 ise al, ≥ 18-20 ise aç.

### 2. High Volatility Events

Haber anları (NFP, FOMC) → spread patlar, slippage artar.

**Çözüm:**

```yaml
filters:
  max_spread_bps: 1.5 # Sıkı filtre
  min_vol_bps_60s: 10 # Aşırı vol'da çık
```

### 3. Fee Sensitivity (Scalp)

10 bps total maliyet → R:R 1.2:1.2 → minimum 15% edge gerek!

**Çözüm:** Sync window = 2 bar (sıkı filtre), cooldown = 5 bar.

---

## 🎓 A/B Test Planı

### Test 1: Sadece RSI vs RSI+MACD

**Hipotez:** MACD eklenmesi win rate'i %5-10 artırır.

**Setup:**

- A: Sadece RSI 50 crossover
- B: RSI 50 + MACD hist cross

**Metrik:** PF, win rate, max DD

### Test 2: Farklı Sync Windows

**Hipotez:** Sıkı sync (≤2 bar) daha yüksek kalite sinyal.

**Setup:**

- A: sync_bars = 2
- B: sync_bars = 5

**Metrik:** Sinyal sayısı vs kalite (PF)

### Test 3: Partial TP (Swing)

**Hipotez:** 1R'de %50 alma → max DD düşer, Sharpe artar.

**Setup:**

- A: Full exit at SL/TP
- B: %50 at 1R, %50 at 2R

**Metrik:** Sharpe, Calmar, Sortino

---

## 📚 Referanslar

- **RSI (14):** Wilder 1978
- **MACD (12/26/9):** Appel 1979
- **ATR stops:** Elder 2002
- **Sync window:** LeviBot internal research 2025

---

## 🛠️ Troubleshooting

### Problem: Çok az sinyal

**Neden:** Sync window çok sıkı veya guardlar çok katı.

**Çözüm:**

```yaml
sync_bars: 5 # 3 → 5 yükselt
filters:
  max_spread_bps: 2.0 # 1.0 → 2.0 gevşet
```

### Problem: Win rate < %50

**Neden:** Gürültülü piyasa, yanlış mod, spread yüksek.

**Çözüm:**

- ADX filtresini ekle: `min_adx: 18`
- Cooldown artır: `cooldown_bars: 10`
- Stop'u sıkılaştır: `sl_atr_mult: 1.0`

### Problem: Overtrading (scalp)

**Neden:** Cooldown yok veya çok kısa.

**Çözüm:**

```yaml
cooldown_bars: 8 # 5 → 8 artır
filters:
  min_vol_bps_60s: 10 # 7 → 10 yükselt
```

---

## ✅ Checklist: Canlıya Geçiş

- [ ] 60+ gün backtest (PF ≥ 1.25)
- [ ] 7-14 gün paper test (PF ≥ 1.15)
- [ ] Grafana dashboard kuruldu
- [ ] Alert'ler aktif (Telegram/Discord)
- [ ] Kill switch hazır
- [ ] Küçük sermaye ile 7 gün test
- [ ] Daily limit set edildi
- [ ] Max drawdown alarmları aktif

---

**Son Güncelleme:** 2025-10-11  
**Versiyon:** 1.0.0  
**Sahip:** LeviBot ML Team 💙


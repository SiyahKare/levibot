# 🚨 LSE Panic Mode

**LeviBot Panic Mode** — Düşüş/şok dönemlerinde sıkı risk yönetimi ile çalışan LSE profili.

## 🎯 Ne Zaman Kullan?

- Market çöküşü / flash crash
- Yüksek volatilite dönemleri
- Likidite krizi / panik satış
- Makro haberler / şok olaylar
- Test sonrası ilk gerçek trading

## 📊 Panic Mode Özellikleri

### Risk Management (Çok Sıkı)

| Parametre           | Normal  | Panic       | Açıklama          |
| ------------------- | ------- | ----------- | ----------------- |
| **Leverage**        | 3x      | **2x**      | Düşük kaldıraç    |
| **Position Size**   | $500    | **$200**    | Küçük pozisyon    |
| **Stop Loss**       | -15 bps | **-25 bps** | Hızlı stop        |
| **Take Profit**     | +25 bps | **+15 bps** | Kısa hedef        |
| **Max Daily DD**    | 2.0%    | **1.5%**    | Sıkı günlük limit |
| **Max Open Trades** | 1       | **1**       | Tek pozisyon      |

### Filters (Çok Seçici)

| Parametre          | Normal  | Panic       | Açıklama             |
| ------------------ | ------- | ----------- | -------------------- |
| **Min Volatility** | 5 bps   | **10 bps**  | Flat market'te pasif |
| **Max Spread**     | 1.0 bps | **0.6 bps** | Çok dar spread       |
| **Max Latency**    | 120 ms  | **80 ms**   | Çok düşük latency    |

### Entry Conditions (Daha Sıkı)

| Parametre            | Normal | Panic   | Açıklama       |
| -------------------- | ------ | ------- | -------------- |
| **ATR k_enter**      | 0.8    | **1.0** | Güçlü momentum |
| **Z-Score enter**    | 1.5    | **2.0** | Ekstrem sapma  |
| **Z-Score lookback** | 120    | **90**  | Kısa hafıza    |

---

## 🚀 Kullanım

### 1. Aktive Et

```bash
make lse-panic-on
```

**Çıktı:**

```
🚨 LSE PANIC MODE AKTIVE EDİLİYOR...
📋 Panic Mode Config:
leverage: 2
quote_budget: 200
hard_stop_bps: 25
take_profit_bps: 15
...
✅ PANIC MODE AKTİF!
```

### 2. Status Kontrol

```bash
make lse-panic-status
```

**Çıktı:**

```
🔍 LSE PANIC MODE STATUS
1️⃣ Engine Health: {running: true, mode: "paper"}
2️⃣ Guards: {vol_ok: true, spread_ok: true, ...}
3️⃣ Recent Trades: 5
4️⃣ PnL: {realized_pnl: 0.2, trades: 12}
```

### 3. Live Monitor

```bash
make lse-panic-watch
```

Gerçek zamanlı guard status + latency + features görürsün.

### 4. Kapat

```bash
make lse-panic-off
```

---

## 📈 Beklenen Davranış

### Panic Mode'da LSE:

- **Flat/düşük vol** → Bekler (min_vol_bps=10)
- **Yüksek spread** → Girmez (max_spread_bps=0.6)
- **Yüksek latency** → Atlar (max_latency_ms=80)
- **Ekstrem Z-score** → Girer (z_enter=2.0)
- **Kısa hedef** → +0.15% TP
- **Hızlı stop** → -0.25% SL

### Normal Mode'da LSE:

- Daha geniş filtreler
- Daha büyük pozisyon ($500)
- Daha uzun hedefler (+0.25%)
- Daha toleranslı spread/latency

---

## 🔧 Config Dosyaları

**Panic Mode:**

```
configs/lse.panic.yaml
```

**Normal Mode:**

```
configs/lse.yaml
```

---

## 📊 Veri Kaydı

Panic mode aktifken trades şuraya kaydedilir:

```
data/lse/panic/
```

Sonra analiz için:

- Feature distributions (panic vs normal)
- PnL by volatility regime
- Entry/exit quality

---

## 💡 Best Practices

1. **Paper'da test et** → Önce simülasyon
2. **Guardrails aktif** → Risk/Guardrails sayfası
3. **Küçük başla** → quote_budget=200
4. **Monitor et** → `make lse-panic-watch`
5. **Normal'e dön** → Piyasa sakinleşince

---

## 🚨 Acil Durum

**Tüm trading'i durdur:**

```bash
make lse-panic-off
curl -X POST http://localhost:8000/admin/emergency-kill
```

**Kill switch** tüm stratejileri anında durdurur.

---

## 🔄 Normal Mode'a Dönüş

```bash
# 1. Panic mode'u kapat
make lse-panic-off

# 2. Normal config'i yükle
curl -X POST http://localhost:8000/lse/params \
  -H 'Content-Type: application/json' \
  -d @configs/lse.yaml

# 3. Yeniden başlat
curl -X POST http://localhost:8000/lse/run \
  -H 'Content-Type: application/json' \
  -d '{"running":true,"mode":"paper"}'
```

---

## 📞 Support

**Monitoring Komutları:**

```bash
make lse-panic-status   # Status
make lse-panic-watch    # Live
make lse-panic-off      # Stop
```

**Log Check:**

```bash
docker compose logs api --tail 50 | grep LSE
```

---

## ✅ Checklist

Panic Mode'a geçmeden önce:

- [ ] API healthy (`make health-check`)
- [ ] Paper mode aktif (mode=paper)
- [ ] Guardrails set (Risk page)
- [ ] Config review (`cat configs/lse.panic.yaml`)
- [ ] Kill switch hazır (`/admin/emergency-kill`)

---

**💙 LeviBot Panic Mode — Kontrollü risk, hızlı reaksiyon**

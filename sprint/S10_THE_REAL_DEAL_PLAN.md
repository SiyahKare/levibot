# 🚀 Sprint-10 — "The Real Deal"

**Tarih:** 15–31 Ekim 2025  
**Owner:** @siyahkare  
**Amaç:** Mock'tan **production modeller + gerçek veri** düzenine geçiş. ccxt/MEXC akışı, gerçek LGBM/TFT eğitimleri, backtesting çerçevesi ve live trading hazırlığı.

---

## 🎯 Hedefler

- **Gerçek veri**: ccxt ile REST + WebSocket; stabil akış
- **Production modeller**: LightGBM (joblib) + TFT (PyTorch Lightning)
- **Backtesting**: 90 günlük geriye dönük simülasyon & rapor
- **Live-Prep**: testnet/paper order flow + kill switch

---

## 📦 Kapsam

**İçerir:** veri ingest, eğitim, inference, backtest, testnet entegrasyon, metrikler  
**Dışında:** On-chain oracle & vault (Sprint-11+), mobil arayüz

---

## 🧩 Epic'ler ve Görevler

### A) Real Data Ingestion (ccxt + Stream)

- [ ] A1: `adapters/mexc_ccxt.py` (REST OHLCV + orderbook snapshot)
- [ ] A2: WebSocket ticker/trades/mini-agg stream + reconnect/backoff
- [ ] A3: Feeder → engine `md` sözlüğüne: `price`, `spread`, `vol`, `texts` (placeholder), `funding`, `oi`
- [ ] A4: Time-sync & gap-fill (minute bars; retry)

**DoD:** 24 saat kesintisiz akış, **dropped < %0.1**, p95 parse < 5ms

### B) Production LGBM (Optuna + joblib)

- [ ] B1: Feature store (Parquet/DuckDB) — leak-safe time split
- [ ] B2: Optuna study (≥ 200 trials), early stop
- [ ] B3: `best_lgbm.pkl` → `EnsemblePredictor` load (joblib)

**DoD:** acc ≥ **%65** (val), leakage **0**, model card oluşturuldu

### C) Production TFT (Lightning)

- [ ] C1: Sequence dataset builder (windowed, scaling)
- [ ] C2: Trainer + early stopping + ckpt + AMP opsiyon
- [ ] C3: `best_tft.pt` → inference wrapper (thread-safe)

**DoD:** p95 inference **≤ 40ms (CPU)**, val-score ≥ baseline LGBM-5%

### D) Backtesting Framework

- [ ] D1: `backtest/runner.py` (vectorized minute sim)
- [ ] D2: Slippage/fee/spread parametrizasyonu
- [ ] D3: Rapor: HTML/MD (Sharpe, Sortino, MDD, turnover)

**DoD:** 90g BTC/ETH raporu; seed-reproducible sonuçlar

### E) Live Trading Prep (testnet)

- [ ] E1: Order adapter (idempotent `clientOrderId`, rate-limit)
- [ ] E2: Circuit breaker & kill switch (global stop bağla)
- [ ] E3: Paper→Testnet staging pipeline (feature flag)

**DoD:** 48 saat testnet/paper sorunsuz yürüyüş; **0 fail order**

---

## 🧪 Test Stratejisi

- **Unit:** adapters, feature store, trainers, backtester (≥ %80)
- **Integration:** ccxt ingest → engine → signal → risk flow
- **Regression gate (CI):** backtest KPI drop > %10 → **fail**

---

## 📈 KPI Hedefleri

| Metrik                     | Hedef  |
| -------------------------- | ------ |
| Accuracy (val)             | ≥ %65  |
| Sharpe (90g backtest)      | ≥ 2.0  |
| Max Drawdown               | ≤ %12  |
| Inference p95 (CPU)        | ≤ 40ms |
| Uptime (paper/testnet 48h) | ≥ %99  |

---

## 📅 Takvim

| Gün       | Epic | Çıktı                          |
| --------- | ---- | ------------------------------ |
| 15–17 Eki | A    | REST+WS akış, feeder stabilize |
| 18–21 Eki | B    | LGBM eğitim + load             |
| 22–24 Eki | C    | TFT eğitim + inference         |
| 25–27 Eki | D    | Backtest + rapor               |
| 28–31 Eki | E    | Testnet run + kill switch      |

---

## 🔐 Riskler & Önlemler

- **WS kesintisi:** exponential backoff + snapshot replay
- **Leakage riski:** time-based split + feature lag testleri
- **Latency spike:** batch predict + cache + async pool
- **Slippage hatası:** spread/fee param'ları; duyarlılık analizi

---

## 🧾 Çıktılar (Dosyalar)

```
backend/src/adapters/mexc_ccxt.py
backend/src/data/feature_store.py
backend/src/ml/train_lgbm_prod.py
backend/src/ml/train_tft_prod.py
backend/src/backtest/runner.py
reports/backtests/90d_{SYMBOL}.html
```

---

## ✅ Definition of Done (Sprint-10)

- [ ] ccxt ingest 24h stabil, dropped < %0.1
- [ ] best_lgbm.pkl & best_tft.pt gerçek eğitimden
- [ ] 90g backtest raporları üretildi (BTC/ETH)
- [ ] Testnet/paper 48h sorunsuz, kill switch doğrulandı
- [ ] KPI hedeflerinin %80'i sağlandı

---

**Prepared by:** @siyahkare  
**Sprint:** S10 — The Real Deal  
**Status:** 🚀 **KICKOFF!**

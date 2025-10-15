# 🚀 LeviBot Development Plan (Next 7 Days)

**Created:** October 15, 2025  
**Status:** 🟢 Active - Immediate Execution  
**Priority:** Production Critical Path

---

## 📊 Mevcut Durum

### ✅ Son 2 Günde Tamamlanan
- ✅ Enterprise AI/Analytics integration (DuckDB, MEXC, JSONL)
- ✅ Modern sidebar navigation (mobile responsive)
- ✅ Current price + price target display (MEXC real-time)
- ✅ Paper trading dashboard ($1,000 start)
- ✅ Real-time updates (5-10s intervals)
- ✅ 3 engines running (BTC/ETH/SOL)

### 🔴 Kritik Eksikler
1. TFT real inference (placeholder kullanılıyor)
2. Sentiment integration (0.0 placeholder)
3. Kill switch tam test edilmemiş
4. Backtest reports yok
5. CI/CD pipeline yok (PR-6)

---

## 🎯 7 Günlük Plan (Oct 15-22)

### Gün 1-2: ML Model Training 🤖
**Görev:** Real LGBM/TFT models

1. LGBM with Optuna
   ```bash
   cd backend && python -m src.ml.train_lgbm_prod
   ```
2. Generate model_card.json
3. TFT sequence builder + training
4. Update symlinks

**Output:** `backend/data/models/2025-10-XX/`

---

### Gün 3: Backtest Framework 📊
**Görev:** 90-day backtest reports

1. Complete `backend/src/backtest/runner.py`
2. Generate HTML reports (Sharpe, drawdown)
3. Run for BTC/ETH/SOL

**Output:** `reports/backtests/90d_BTCUSDT.html`

---

### Gün 4: Kill Switch Testing 🛡️
**Görev:** Emergency stop validation

1. Test `/live/kill` endpoint
2. Simulate high error rate
3. Document recovery procedures
4. Add frontend kill switch button

---

### Gün 5-6: Monitoring & Alerts 📈
**Görev:** Grafana dashboards + Prometheus alerts

1. Create 3 custom dashboards
2. Configure 15+ alert rules
3. Test alert delivery

---

### Gün 7: Integration Testing 🧪
**Görev:** End-to-end validation

1. Run smoke tests
2. 24h stability test
3. Performance benchmarks

---

## 📋 İmmediate Actions (Today)

```bash
# 1. Start paper trading monitoring
./scripts/smoke_test_integration.sh

# 2. Check current status
curl http://localhost:8000/health
curl http://localhost:8000/engines

# 3. Begin LGBM training
cd backend
python -m src.ml.train_lgbm_prod
```

---

## 🎯 Success Metrics

- Inference p95 < 50ms
- Uptime > 99%
- Backtest Sharpe ≥ 2.0
- Kill switch response < 1s
- Zero crashes

---

**Next Review:** October 18, 2025

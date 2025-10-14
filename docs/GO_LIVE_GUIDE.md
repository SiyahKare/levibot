# 🚀 GO-LIVE GUIDE - 48-Hour Canary Marathon

**Para Kazan, Koru, Büyüt!** 💰

---

## 🎯 Hedef

48 saatlik canary-paper marathon ile production'a güvenli geçiş:

- ✅ Canary deployment (10% traffic)
- ✅ Shadow logging (risk-free validation)
- ✅ Auto-monitoring (drift + ECE + staleness)
- ✅ Promote criteria (metrik-based decision)

---

## 🚦 HEMEN BAŞLA (Tek Komut)

```bash
bash backend/scripts/start_canary_marathon.sh
```

Bu script:

1. ✅ Son kritik kontrol (ECE, policy, registry)
2. ✅ Go-live checklist (10 dakika)
3. ✅ Drift check (PSI/KS)
4. ✅ Ensemble tuning
5. ✅ Canary enable (10%)
6. ✅ API restart
7. ✅ Monitoring başlat

**Output:** Marathon başladı, 48 saat izle!

---

## 📊 Monitoring (48 Saat Boyunca)

### Real-Time Logs

```bash
# Shadow predictions
tail -f backend/data/logs/shadow/predictions_*.jsonl

# Shadow trades
tail -f backend/data/logs/shadow/trades_*.jsonl

# API logs
docker logs -f levibot-api-1
```

### Health Checks (Her 4-6 Saatte)

```bash
# Healthz
curl http://localhost:8000/healthz | jq

# Automation status
curl http://localhost:8000/automation/status | jq

# ML predictions
curl "http://localhost:8000/ml/predict?symbol=BTCUSDT" | jq
curl "http://localhost:8000/ml/predict_deep?symbol=BTCUSDT" | jq
curl "http://localhost:8000/ml/predict_ensemble?symbol=BTCUSDT" | jq
```

### Drift + Ensemble (Otomatik Cron)

```bash
# Manuel çalıştırma (isteğe bağlı)
python backend/scripts/drift_check.py
python backend/scripts/ensemble_tuner.py
```

### Grafana Dashboard

```
http://localhost:3000

Dashboard: ML Production
- Model ECE (alert if > 0.06)
- Feature Staleness (alert if > 1800s)
- Drift PSI (top 5 features)
- Drift Events (critical alert)
- Ensemble Weights
- Model Uncertainty
- Paper PnL (1D, 7D)
- Sharpe, MaxDD
```

---

## 🛡️ Fail-Safe Commands

### Kill-Switch (Acil Durdur)

```bash
# Enable
curl -X POST "http://localhost:8000/ml/kill?enabled=true"

# Verify
curl "http://localhost:8000/ml/predict?symbol=BTCUSDT" | jq .signal
# Should return HOLD when kill-switch is on

# Disable
curl -X POST "http://localhost:8000/ml/kill?enabled=false"
```

### ECE Patladı (> 0.07) → Policy Sıkılaştır

```bash
# Check current ECE
jq '.current.calibration.ece_calibrated' backend/data/registry/model_registry.json

# Tighten thresholds (+0.01 entry, -0.01 exit)
jq '.current.policy.entry_threshold += 0.01 |
    .current.policy.exit_threshold -= 0.01' \
  backend/data/registry/model_registry.json > /tmp/registry.json

mv /tmp/registry.json backend/data/registry/model_registry.json

# Restart API
docker compose restart api
```

### Drift Yüksek (PSI > 0.3) → Auto-Retrain

```bash
# Kill-switch ON (auto by drift_check.py if PSI > 0.3)
curl -X POST "http://localhost:8000/ml/kill?enabled=true"

# Retrain
python backend/scripts/train_ml_model.py --symbol BTCUSDT --days 60
python backend/scripts/calibrate_and_sweep.py

# Verify improvement
python backend/scripts/drift_check.py

# If OK, kill-switch OFF
curl -X POST "http://localhost:8000/ml/kill?enabled=false"
```

### Staleness Spike (> 1800s)

```bash
# Check staleness
curl http://localhost:8000/healthz | jq .feature_staleness_sec

# If > 1800s:
# 1. Kill-switch ON
curl -X POST "http://localhost:8000/ml/kill?enabled=true"

# 2. Re-ingest data
python backend/ml/feature_store/ingest_multi.py

# 3. Verify
curl http://localhost:8000/healthz | jq .feature_staleness_sec

# 4. If OK, kill-switch OFF
curl -X POST "http://localhost:8000/ml/kill?enabled=false"
```

---

## 📈 T+48H Evaluation

```bash
bash backend/scripts/evaluate_marathon.sh
```

### Evaluation Criteria

| Metric          | Requirement                          | Weight    |
| --------------- | ------------------------------------ | --------- |
| **ECE**         | ≤ 0.05 (target), ≤ 0.06 (acceptable) | Critical  |
| **Staleness**   | ≤ 1800s (2× bar for 15m)             | Critical  |
| **Drift**       | PSI ≤ 0.2 on all features            | Critical  |
| **Shadow Data** | ≥ 20 trades for analysis             | Important |
| **API Health**  | /healthz OK                          | Critical  |

**Pass Criteria:** 4/5 checks passed → PROMOTE READY

### Promote Decision

```
✅ PROMOTE if:
  - Evaluation script: ≥ 4/5 checks passed
  - Sharpe_canary ≥ Sharpe_prod + 0.2 (manual analysis)
  - MaxDD_canary ≤ 0.9 × MaxDD_prod (manual analysis)
  - No critical incidents during 48h

⚠️  EXTEND if:
  - 3/5 checks passed
  - Close to criteria but need more data
  - Extend to 72h

❌ ROLLBACK if:
  - ≤ 2/5 checks passed
  - Critical drift/staleness events
  - Sharpe_canary < Sharpe_prod - 0.3
```

---

## 🚀 Promote (If Criteria Met)

```bash
# 1. Promote model
python backend/scripts/promote_model.py \
  backend/models/deep_tfm_BTCUSDT_final.pt \
  "T+48h marathon passed, ECE=0.042, Sharpe=1.87"

# 2. Disable canary (use new model 100%)
jq '.enabled = false' backend/data/registry/canary_policy.json > /tmp/canary.json
mv /tmp/canary.json backend/data/registry/canary_policy.json

# 3. Restart API
docker compose restart api

# 4. Verify
curl "http://localhost:8000/ml/predict?symbol=BTCUSDT" | jq

# 5. Monitor for next 24h closely
# Then gradually increase paper → live
```

---

## 📋 Cron Jobs (Production)

```bash
# View templates
bash backend/scripts/cron_setup.sh

# Install
crontab -e

# Add these lines:
*/15 * * * * cd /Users/onur/levibot && python backend/scripts/drift_check.py >> /tmp/drift_check.log 2>&1
0 * * * * cd /Users/onur/levibot && python backend/scripts/ensemble_tuner.py >> /tmp/ensemble_tuner.log 2>&1
0 */6 * * * cd /Users/onur/levibot && python backend/ml/feature_store/ingest_multi.py >> /tmp/ingest.log 2>&1
0 2 * * 0 cd /Users/onur/levibot && python backend/scripts/train_ml_model.py --symbol BTCUSDT --days 45 >> /tmp/retrain.log 2>&1
```

---

## 🧪 Testing Checklist

### Pre-Marathon (Before Start)

- [ ] Sprint-1 smoke test passed
- [ ] Sprint-2 deep models trained
- [ ] Model registry has calibration + policy
- [ ] ECE ≤ 0.06
- [ ] Feature staleness < 1800s
- [ ] Drift check PSI < 0.2
- [ ] API /healthz OK
- [ ] Grafana dashboard configured

### During Marathon (Every 6-12h)

- [ ] Feature staleness < 1800s
- [ ] ECE < 0.06
- [ ] No critical drift events
- [ ] Shadow logs growing
- [ ] API healthy
- [ ] No repeated errors in logs

### Post-Marathon (T+48h)

- [ ] Run evaluation script
- [ ] Manual shadow log analysis
- [ ] Sharpe comparison (canary vs prod)
- [ ] MaxDD comparison
- [ ] Review Grafana metrics
- [ ] Make promote/extend/rollback decision

---

## 💰 Expected Results

### Paper Trading Performance (T+48h)

| Metric        | Target | Good      | Excellent |
| ------------- | ------ | --------- | --------- |
| **Sharpe**    | > 1.2  | 1.5-1.8   | > 2.0     |
| **Win Rate**  | > 52%  | 55-58%    | > 60%     |
| **Max DD**    | < 15%  | 10-13%    | < 10%     |
| **Avg Trade** | > 0%   | 0.5-1%    | > 1.5%    |
| **ECE**       | < 0.06 | 0.03-0.05 | < 0.03    |

### System Health (Continuous)

| Metric                | Target  | Alert Threshold |
| --------------------- | ------- | --------------- |
| **Feature Staleness** | < 900s  | > 1800s         |
| **API Latency**       | < 500ms | > 2000ms        |
| **Drift PSI**         | < 0.15  | > 0.25          |
| **ECE**               | < 0.05  | > 0.06          |
| **Memory Usage**      | < 2GB   | > 4GB           |

---

## 🔥 Common Issues

### "Shadow logs empty"

**Cause:** No trades executed yet (not enough signals or kill-switch on)

**Fix:**

```bash
# Check kill-switch
ls backend/data/ml_kill_switch.flag

# Check automation status
curl http://localhost:8000/automation/status | jq

# Manually trigger prediction
curl "http://localhost:8000/ml/predict?symbol=BTCUSDT" | jq
```

### "Drift check fails immediately"

**Cause:** Not enough recent data vs training data

**Fix:**

```bash
# Re-ingest last 7 days
python backend/ml/feature_store/ingest_multi.py

# Retrain with recent data
python backend/scripts/train_ml_model.py --symbol BTCUSDT --days 30
python backend/scripts/calibrate_and_sweep.py
```

### "API predictions timeout"

**Cause:** CoinGecko rate limit or model loading slow

**Fix:**

```bash
# Check API logs
docker logs levibot-api-1 --tail 100

# Restart API
docker compose restart api

# Check healthz
curl http://localhost:8000/healthz | jq
```

---

## 📞 Emergency Contacts

### System Down

1. Check Docker: `docker ps`
2. Check logs: `docker logs levibot-api-1 --tail 200`
3. Restart: `docker compose restart api`
4. If persists: `docker compose down && docker compose up -d --build`

### Critical Drift

1. Enable kill-switch: `curl -X POST "http://localhost:8000/ml/kill?enabled=true"`
2. Analyze drift: `python backend/scripts/drift_check.py`
3. Retrain if needed
4. Re-evaluate before resuming

### Poor Performance

1. Review shadow logs manually
2. Check ECE: might need recalibration
3. Analyze losing trades: look for patterns
4. Consider extending marathon or rolling back

---

## 🎯 Success Criteria Summary

✅ **Ready to Promote:**

- 48h completed
- 4/5 evaluation checks passed
- Sharpe > 1.5
- MaxDD < 13%
- ECE < 0.05
- No critical incidents

🎉 **When promoted:**

- Continue paper trading with new model
- Monitor closely for 7 days
- Gradually scale from paper → live
- Keep kill-switch ready

---

**Paşam, GO-LIVE rehberi hazır!** 🚀

**Başlatmak için:**

```bash
bash backend/scripts/start_canary_marathon.sh
```

**Para kazan, koru, büyüt! 💰🔥**

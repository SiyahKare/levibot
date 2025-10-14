# 🧠 AI-Powered Trading Engine

**LeviBot AI Trading Engine** - Makine öğrenmesi ve teknik analiz ile otomatik trading sistemi.

---

## 🎯 Genel Bakış

AI Trading Engine, **random trade** yapmaz. Bunun yerine:

1. **Geçmiş fiyat verilerini** analiz eder
2. **Technical indicators** hesaplar (RSI, MA, Volatility)
3. **Momentum** ve **trend** sinyalleri değerlendirir
4. **ML-based confidence score** hesaplar
5. Sadece **yüksek confidence** ile trade açar
6. **Risk yönetimi** ile pozisyonları yönetir

---

## 🤖 Nasıl Çalışır?

### 1. **Price History Tracking**
- Her sembol için sürekli fiyat geçmişi tutar
- Son 100 fiyat noktasını saklar
- Her cycle'da güncel fiyatları çeker

### 2. **Feature Engineering**
Her sembol için hesaplanan metrikler:

| Feature | Açıklama | Ağırlık |
|---------|----------|---------|
| **Momentum** | 1, 5, 10 periyot returns | %40 |
| **Trend vs MA** | Fiyat - Moving Average uzaklığı | %25 |
| **RSI** | Relative Strength Index | %20 |
| **Volatility** | Fiyat oynaklığı | %15 |

### 3. **ML Scoring**
```python
score = 0.5  # Başlangıç (nötr)

# Momentum (40%)
if ret_1 > 0.1%  → +0.10
if ret_5 > 0.5%  → +0.15
if ret_10 > 1.0% → +0.15

# Trend (25%)
if price > MA20 → +0.10 to +0.15

# RSI (20%)
if 30 < RSI < 70   → +0.05  # Nötr bölge
if RSI < 30        → +0.15  # Oversold (AL!)
if RSI > 70        → -0.10  # Overbought (KAÇIN!)

# Volatility (15%)
if volatility optimal → +0.10
if volatility risky   → -0.05
```

**Sonuç**: Score 0-1 arası (1 = %100 buy confidence)

### 4. **Decision Logic**

```python
# BUY Kararı
if ML_Score >= 0.65:  # Min confidence threshold
    position_size = dynamic_sizing(confidence)
    open_position()
    
# SELL Kararı
if pnl <= -3%:     # Stop Loss
    close_position()
elif pnl >= 5%:    # Take Profit
    close_position()
elif ML_Score < 0.40:  # ML sell signal
    close_position()
```

---

## 📊 Risk Management

### Position Sizing
- **Base**: $50-150 (dinamik)
- **Confidence multiplier**: 0.7x - 1.7x
- **Formül**: `notional = base * (0.7 + (confidence - 0.65) * 2)`

Örnek:
- Confidence 0.65 → $87 (0.7x)
- Confidence 0.75 → $107 (1.0x)
- Confidence 0.85 → $127 (1.3x)

### Stop Loss & Take Profit
- **Stop Loss**: 3% (koruma)
- **Take Profit**: 5% (kar)
- **ML Exit**: Score < 0.40 (sinyal bozulması)

### Position Limits
- **Max Positions**: 3 (aynı anda)
- **Max Notional**: $150 (tek trade)
- **Min Confidence**: 65% (min güven)

---

## 🚀 Kullanım

### API Endpoints

#### 1. Status Kontrolü
```bash
curl http://localhost:8000/automation/status
```

Response:
```json
{
  "ok": true,
  "mode": "AI-Powered",
  "enabled": true,
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"],
  "max_positions": 3,
  "min_confidence": 0.65,
  "cycle_count": 42,
  "trades_today": 8
}
```

#### 2. Real-Time Predictions
```bash
curl http://localhost:8000/automation/predictions
```

Response:
```json
{
  "predictions": {
    "BTCUSDT": {
      "should_buy": true,
      "confidence": 0.72,
      "ml_score": 0.72,
      "rsi": 45.3,
      "volatility": 0.021,
      "returns": {
        "ret_1": 0.003,
        "ret_5": 0.015,
        "ret_10": 0.028
      }
    }
  }
}
```

#### 3. Start/Stop
```bash
# Başlat
curl -X POST http://localhost:8000/automation/start

# Durdur
curl -X POST http://localhost:8000/automation/stop

# Manuel cycle
curl -X POST http://localhost:8000/automation/trigger
```

#### 4. Config Güncelleme
```bash
curl -X PUT http://localhost:8000/automation/config \
  -H "Content-Type: application/json" \
  -d '{
    "min_confidence": 0.70,
    "max_positions": 5,
    "stop_loss_pct": 0.04,
    "take_profit_pct": 0.08
  }'
```

---

## 📈 Panel Entegrasyonu

### Paper Trading Dashboard

Panel'de gösterilen:
- ✅ Real-time portfolio stats
- ✅ AI predictions ve confidence scores
- ✅ Trade history with reasoning
- ✅ P&L tracking
- ❌ AI insights (TODO)

### Eklenecek Özellikler:
```typescript
// AI Insights Component
{
  symbol: "BTCUSDT",
  ml_score: 0.72,
  should_buy: true,
  indicators: {
    rsi: 45.3,
    volatility: 0.021,
    momentum: "STRONG_UP"
  },
  reasoning: "Strong upward momentum with optimal volatility"
}
```

---

## 🔬 Technical Details

### Indicators Hesaplama

#### RSI (Relative Strength Index)
```python
gains = [max(0, price[i] - price[i-1]) for i in range(1, len(prices))]
losses = [max(0, price[i-1] - price[i]) for i in range(1, len(prices))]

avg_gain = sum(gains) / len(gains)
avg_loss = sum(losses) / len(losses)

rs = avg_gain / avg_loss
rsi = 100 - (100 / (1 + rs))
```

#### Moving Average
```python
ma_20 = sum(prices[-20:]) / 20
```

#### Volatility
```python
returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
volatility = std_dev(returns)
```

---

## 🎓 Model Training (Future)

Şu an: **Rule-based ML scoring**

Gelecek:
1. **XGBoost model** training
2. **Historical data** collection
3. **Backtesting** framework
4. **Model retraining** (weekly)

```python
# Future: Trained XGBoost model
model = xgboost.XGBClassifier()
model.fit(X_train, y_train)

# Real-time inference
features = extract_features(symbol)
probability = model.predict_proba(features)[0, 1]
```

---

## 🎯 Performance Metrics

Track edilecek:
- **Win Rate**: % profitable trades
- **Avg Return**: Ortalama kazanç
- **Sharpe Ratio**: Risk-adjusted return
- **Max Drawdown**: En büyük kayıp
- **Total PnL**: Toplam kar/zarar

---

## ⚙️ Configuration

### Environment Variables
```bash
# AI Engine Settings
AI_TRADING_ENABLED=true
AI_MIN_CONFIDENCE=0.65
AI_MAX_POSITIONS=3
AI_CYCLE_INTERVAL_MIN=2

# Risk Management
AI_STOP_LOSS_PCT=0.03
AI_TAKE_PROFIT_PCT=0.05
AI_MIN_NOTIONAL=50
AI_MAX_NOTIONAL=150
```

---

## 🔍 Monitoring

### Container Logs
```bash
# AI trading logs
docker logs -f levibot-api | grep "AI-"

# Output:
⚡ AI Trading Cycle #42 [20:15:03]
   Open Positions: 2 | Trades Today: 8
   🎯 Best Opportunity: BTCUSDT (confidence: 72.00%)
🤖 AI-Trade: BUY BTCUSDT $107 @ $62150.00 | Confidence: 72.00%
🤖 AI-Close: SELL ETHUSDT @ $4489.50 | 🟢 PnL: $12.35 (2.84%) | TAKE_PROFIT
```

### Metrics (Prometheus)
```promql
# Trade count
levibot_ai_trades_total{side="buy|sell", reason="ml_signal|stop_loss|take_profit"}

# Confidence distribution
levibot_ai_confidence_histogram

# P&L
levibot_ai_pnl_total
```

---

## 📚 Best Practices

### 1. Warm-up Period
İlk 20-30 cycle boyunca yeterli veri toplanır:
- Price history build-up
- Indicator calculation
- Confidence stabilization

**İlk 10 dakika:** Sadece veri toplama (no trades)

### 2. Confidence Tuning
- **Conservative**: `min_confidence = 0.75` (daha az trade, daha güvenli)
- **Moderate**: `min_confidence = 0.65` (balanced)
- **Aggressive**: `min_confidence = 0.55` (daha çok trade, riskli)

### 3. Backtesting
Gerçek trade yapmadan önce:
```bash
# Backtest mode (simulated)
curl -X POST http://localhost:8000/automation/backtest \
  -d '{"start_date": "2024-10-01", "end_date": "2024-10-07"}'
```

---

## 🚨 Troubleshooting

### "No opportunities above confidence threshold"
- Piyasa nötr/sideways
- Confidence threshold çok yüksek
- Yeterli price history yok

**Çözüm**: Birkaç cycle bekle veya threshold'u düşür

### "Insufficient balance"
- Portfolio boş veya düşük
- Max notional çok yüksek

**Çözüm**: Portfolio reset veya notional ayarla

### Çok fazla loss
- Market volatility yüksek
- Stop loss çok dar

**Çözüm**: Stop loss genişlet veya pause

---

## 📞 Support

- **Docs**: `/docs/AI_TRADING.md`
- **API**: `http://localhost:8000/docs` (Swagger)
- **Logs**: `docker logs levibot-api`

---

**🎉 Happy AI Trading!** 🤖📈

# 🧭 Sprint-9: AI Fusion & Engine Upgrade

**Kod Adı:** `Gemma Fusion`  
**Tarih:** 14–31 Ekim 2025  
**Durum:** 🚧 IN PROGRESS  
**Owner:** @siyahkare (Onur Mutlu / NovaBaron)

---

## 🎯 Sprint Hedefi

LeviBot'un **multi-symbol** işlem kapasitesini stabilize etmek ve ilk **AI Fusion (Gemma + LightGBM + TFT)** tahmin katmanını devreye almak.

**Başarı Kriterleri:**

- ✅ 10-15 sembol paralel çalışabiliyor
- ✅ AI Fusion modeli %60+ doğruluk sağlıyor
- ✅ Otomatik retrain döngüsü çalışıyor
- ✅ Risk yönetimi aktif ve dengeli
- ✅ CI/CD pipeline production-ready

---

## ⚙️ Epic 1: Multi-Engine Stabilization

**Amaç:** Her sembolün kendi işlem döngüsünde paralel çalışması.

### Görevler

#### 1.1: Engine Manager Refactor

- [ ] **Task:** `backend/src/engine_manager.py` refactor
  - [ ] Multiprocessing veya asyncio kullanarak paralel engine yönetimi
  - [ ] Engine lifecycle: `start()`, `stop()`, `restart()`, `health_check()`
  - [ ] Symbol bazlı engine spawn/kill mekanizması
  - [ ] Shared state için Redis/file-based koordinasyon
  - [ ] Process monitoring (psutil veya native)

**Acceptance Criteria:**

```python
# Her sembol için independent engine
engines = {
    'BTCUSDT': Engine(symbol='BTCUSDT', config=...),
    'ETHUSDT': Engine(symbol='ETHUSDT', config=...),
    # ... 10-15 sembol
}
# manager.start_all() → hepsi parallel başlar
# manager.health_check() → canlı olanları gösterir
```

#### 1.2: Engine Registry & Config

- [ ] **Task:** `backend/data/engine_registry.json` oluştur
  - [ ] Symbol bazlı state tracking
  ```json
  {
    "BTCUSDT": {
      "status": "running",
      "pid": 12345,
      "uptime": 3600,
      "last_trade": "2025-10-14T12:30:00Z",
      "pnl": 150.0
    }
  }
  ```
  - [ ] Config per symbol (risk, size, strategy)
  - [ ] Hot reload capability (config değişince restart etmeden güncelle)

#### 1.3: Health Monitor API

- [ ] **Task:** FastAPI endpoint `/engines/status`
  - [ ] Tüm engine'lerin durumunu listele
  - [ ] Response format:
  ```json
  {
    "total": 12,
    "running": 11,
    "stopped": 1,
    "crashed": 0,
    "engines": [
      { "symbol": "BTCUSDT", "status": "running", "uptime": "2h15m" },
      { "symbol": "ETHUSDT", "status": "crashed", "last_error": "..." }
    ]
  }
  ```

#### 1.4: Crash Recovery Loop

- [ ] **Task:** `restart_engine(symbol)` otomatik iyileşme
  - [ ] Watchdog process (her 30s health check)
  - [ ] Crashed engine detection
  - [ ] Auto-restart with exponential backoff
  - [ ] Max restart limit (5 başarısız → permanent stop)
  - [ ] Alert (Telegram/Slack) on crash

#### 1.5: Logging Separation

- [ ] **Task:** Symbol bazlı log dosyaları
  - [ ] `backend/data/logs/engine-BTCUSDT-{date}.jsonl`
  - [ ] `backend/data/logs/engine-ETHUSDT-{date}.jsonl`
  - [ ] Centralized aggregation (Loki/ClickHouse için)
  - [ ] Log rotation (daily, max 30 days)

**Test Command:**

```bash
# Terminal 1: Manager başlat
python -m backend.src.engine_manager --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Terminal 2: Health check
watch -n 10 "curl -s localhost:8000/engines/status | jq"

# Terminal 3: Crash simulation
kill -9 $(pgrep -f "engine-BTCUSDT")
# Watch için otomatik restart'ı gözlemle
```

**Epic 1 KPI:**

- Uptime: ≥99%
- Crash recovery time: <10s
- Max concurrent engines: 15+

---

## 🧠 Epic 2: AI Fusion Layer — "Gemma Brain v1"

**Amaç:** Modelin fiyat + duygu + zincir verisini birleştirerek karar üretmesi.

### Görevler

#### 2.1: Sentiment Extractor (Gemma-3 API)

- [ ] **Task:** `backend/ml/features/sentiment_extractor.py`
  - [ ] Gemma-3 API entegrasyonu (Google AI Studio veya self-hosted)
  - [ ] Input: news headline/tweet text
  - [ ] Output: sentiment score (-1.0 to +1.0)
  - [ ] Features:
    - [ ] Text preprocessing (remove URLs, special chars)
    - [ ] Batch processing (100 texts/request)
    - [ ] Caching (Redis, TTL 1h)
    - [ ] Rate limiting (Google API limits)

**Example Usage:**

```python
from ml.features.sentiment_extractor import GemmaSentiment

sentiment = GemmaSentiment()
score = sentiment.analyze("Bitcoin ETF approval expected soon!")
# score: 0.78 (positive)
```

#### 2.2: OnChain Data Fetcher

- [ ] **Task:** `backend/ml/features/onchain_fetcher.py`
  - [ ] Dune Analytics API entegrasyonu
  - [ ] Nansen API (opsiyonel, paid)
  - [ ] Metrics:
    - [ ] `active_addresses_24h` (int)
    - [ ] `exchange_inflow_usd` (float)
    - [ ] `exchange_outflow_usd` (float)
    - [ ] `whale_transactions_count` (int)
    - [ ] `funding_rate` (float, from exchange API)
  - [ ] Caching (Redis, TTL 5min)
  - [ ] Fallback values (API down → use last known)

**Example Query (Dune):**

```sql
SELECT
  COUNT(DISTINCT from_address) as active_addresses,
  SUM(value_usd) as volume_usd
FROM ethereum.transactions
WHERE block_time >= NOW() - INTERVAL '24 hours'
  AND to_address IN (SELECT address FROM exchange_addresses)
```

#### 2.3: Ensemble Predictor (Fusion Model)

- [ ] **Task:** `backend/ml/models/ensemble_predictor.py`
  - [ ] Model architecture:
    ```
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
    │  LightGBM   │  │     TFT      │  │   Sentiment  │
    │  (OHLCV)    │  │ (Time Series)│  │   (Gemma)    │
    └──────┬──────┘  └──────┬───────┘  └──────┬───────┘
           │                │                 │
           └────────────────┴─────────────────┘
                            │
                    ┌───────▼────────┐
                    │ Weighted Fusion│
                    │ w=[0.5,0.3,0.2]│
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ Final Prediction│
                    │ (prob_up, conf) │
                    └────────────────┘
    ```
  - [ ] Training pipeline:
    - [ ] Feature alignment (same timestamps)
    - [ ] Weight optimization (grid search or Optuna)
    - [ ] Backtesting (2023-2024 data)
  - [ ] Inference:
    - [ ] Real-time feature fetch (<500ms)
    - [ ] Ensemble voting
    - [ ] Confidence score (0-1)

**Model Config:**

```yaml
ensemble:
  models:
    - name: lightgbm
      weight: 0.5
      features: [ohlcv, volume, indicators]
    - name: tft
      weight: 0.3
      features: [price_history, volatility]
    - name: sentiment
      weight: 0.2
      features: [news_score, social_score]
  voting: weighted_average
  threshold: 0.6 # Min confidence to trade
```

#### 2.4: Auto Tuner (Hyperparameter Optimization)

- [ ] **Task:** `backend/ml/auto_tuner.py`
  - [ ] Framework: Optuna or AutoGluon
  - [ ] Objective: Maximize Sharpe ratio (backtest)
  - [ ] Search space:
    ```python
    {
      'lgbm_depth': [3, 7],
      'lgbm_lr': [0.01, 0.1],
      'tft_hidden': [32, 128],
      'ensemble_weights': [[0.3, 0.4, 0.3], [0.5, 0.3, 0.2], ...]
    }
    ```
  - [ ] 100 trials
  - [ ] Best model save: `backend/ml/models/best_ensemble.pkl`

**Run Command:**

```bash
python -m ml.auto_tuner \
  --symbol BTCUSDT \
  --start-date 2023-01-01 \
  --end-date 2024-10-01 \
  --trials 100 \
  --objective sharpe
```

**Epic 2 Test:**

```bash
python -m ml.run_fusion_test \
  --symbol BTCUSDT \
  --lookback 500
```

**Epic 2 KPI:**

- Model accuracy (classification): ≥60%
- Sharpe ratio (backtest): ≥1.5
- Inference latency: <400ms (P95)
- Sentiment API uptime: ≥99%

---

## 🛡️ Epic 3: Risk Manager v2

**Amaç:** Dinamik pozisyon boyutu ve global guard sistemi.

### Görevler

#### 3.1: Risk Manager Core

- [ ] **Task:** `backend/risk/manager.py`

  - [ ] Position sizing:

  ```python
  def calculate_position_size(
      symbol: str,
      equity: float,
      volatility: float,  # ATR or std
      max_risk_pct: float = 0.02
  ) -> float:
      """
      Kelly criterion veya fixed fractional sizing.

      position_usd = equity * max_risk_pct / volatility_normalized
      """
      pass
  ```

  - [ ] Global stop trigger:

  ```python
  def global_stop_trigger() -> bool:
      """
      Tüm sembollerdeki günlük PnL toplamı -3% geçerse True.
      """
      daily_pnl = sum(engine.get_daily_pnl() for engine in engines)
      return daily_pnl < -0.03 * total_equity
  ```

  - [ ] Symbol-level limits:
    - Max position per symbol: 20% of equity
    - Max concurrent positions: 15
    - Max correlated positions: 5 (BTC + alts)

#### 3.2: Risk Policy Config

- [ ] **Task:** `backend/risk/policy.yaml`

  ```yaml
  risk_policy:
    max_daily_loss_pct: 3.0
    max_symbol_risk_pct: 0.2
    max_concurrent_positions: 15
    rebalance_frequency: weekly

    correlation_groups:
      btc_alts: [BTCUSDT, ETHUSDT, SOLUSDT]
      eth_ecosystem: [ETHUSDT, MATICUSDT, LINKUSDT]

    position_sizing:
      method: kelly # or fixed_fractional
      kelly_fraction: 0.5
      min_position_usd: 10
      max_position_usd: 1000
  ```

#### 3.3: Portfolio Rebalancer

- [ ] **Task:** `backend/risk/rebalancer.py`
  - [ ] Weekly portfolio review
  - [ ] Underweight/overweight detection
  - [ ] Auto-adjust position sizes
  - [ ] Cron: `0 2 * * 1` (Monday 2 AM)

**Epic 3 Test:**

```bash
# Simulate 10 parallel positions
python -m risk.test_manager --symbols 10 --equity 10000

# Check global stop
python -m risk.test_global_stop --daily-loss -4.0
# Expected: All engines stopped
```

**Epic 3 KPI:**

- Max drawdown: ≤12%
- Symbol risk balance: <±5% deviation
- Global stop trigger time: <5s

---

## 🧪 Epic 4: CI/CD Pipeline Refresh

**Amaç:** Kod stabilitesini ve otomatik testleri devreye almak.

### Görevler

#### 4.1: GitHub Actions Workflow

- [ ] **Task:** `.github/workflows/deploy.yml`

  ```yaml
  name: Deploy LeviBot

  on:
    push:
      branches: [main, develop]

  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Setup Python
          uses: actions/setup-python@v4
          with:
            python-version: "3.11"
        - name: Install dependencies
          run: pip install -r backend/requirements.txt
        - name: Lint
          run: ruff check backend/
        - name: Type check
          run: mypy backend/src
        - name: Unit tests
          run: pytest backend/tests/ -v --disable-warnings
        - name: Integration tests
          run: pytest backend/tests/integration/ -v

    build:
      needs: test
      runs-on: ubuntu-latest
      steps:
        - name: Build Docker image
          run: docker build -t levibot:${{ github.sha }} .
        - name: Push to registry
          run: docker push levibot:${{ github.sha }}

    deploy:
      needs: build
      runs-on: ubuntu-latest
      steps:
        - name: SSH deploy
          run: |
            ssh user@server "docker pull levibot:${{ github.sha }}"
            ssh user@server "docker compose up -d"
  ```

#### 4.2: Test Coverage Expansion

- [ ] **Task:** Genişletilmiş test suite
  - [ ] `tests/test_ai.py` (AI Fusion)
    - [ ] Sentiment extraction test
    - [ ] OnChain fetcher mock test
    - [ ] Ensemble prediction test
  - [ ] `tests/test_engine.py` (Engine Manager)
    - [ ] Engine lifecycle test
    - [ ] Crash recovery test
    - [ ] Multi-engine concurrent test
  - [ ] `tests/test_risk.py` (Risk Manager)
    - [ ] Position sizing test
    - [ ] Global stop test
    - [ ] Rebalance test
  - [ ] `tests/integration/test_clickhouse.py`
    - [ ] Event logging test
    - [ ] Query performance test
  - [ ] `tests/integration/test_prometheus.py`
    - [ ] Metrics collection test
    - [ ] Alert rule test

**Coverage Target:** ≥80%

#### 4.3: Docker Optimization

- [ ] **Task:** Multi-stage build

  ```dockerfile
  # Build stage
  FROM python:3.11-slim as builder
  WORKDIR /app
  COPY backend/requirements.txt .
  RUN pip install --user -r requirements.txt

  # Runtime stage
  FROM python:3.11-slim
  WORKDIR /app
  COPY --from=builder /root/.local /root/.local
  COPY backend/ ./backend/
  ENV PATH=/root/.local/bin:$PATH
  CMD ["uvicorn", "backend.src.app.main:app", "--host", "0.0.0.0"]
  ```

  - [ ] Image size: <500MB
  - [ ] Build time: <5min

**Epic 4 Test:**

```bash
pytest -v --disable-warnings --cov=backend --cov-report=html
```

**Epic 4 KPI:**

- Test coverage: ≥80%
- CI/CD pipeline time: <10min
- Docker image size: <500MB

---

## 🔄 Epic 5: Nightly AutoML & Retrain Loop

**Amaç:** Modelin her gece kendi kendine yeniden eğitilmesi.

### Görevler

#### 5.1: Nightly Retrain Script

- [ ] **Task:** `backend/scripts/nightly_retrain.sh`

  ```bash
  #!/bin/bash
  set -e

  echo "[$(date)] Starting nightly retrain..."

  # 1. Veri toplama (son 24h)
  python -m ml.data_collector --days 1

  # 2. Feature engineering
  python -m ml.feature_pipeline --update

  # 3. AutoML tuner
  python -m ml.auto_tuner \
    --symbol BTCUSDT \
    --start-date $(date -d '30 days ago' +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d) \
    --trials 50 \
    --objective sharpe

  # 4. Model deployment
  cp ml/models/best_ensemble.pkl ml/models/production.pkl
  ln -sf production.pkl ml/models/current.pkl

  # 5. Validation
  python -m ml.validate_model --model current.pkl

  # 6. Notification
  python -m alerts.send_telegram "✅ Nightly retrain complete. New model deployed."

  echo "[$(date)] Retrain complete."
  ```

#### 5.2: Cron Setup

- [ ] **Task:** Crontab entry
  ```cron
  # Nightly retrain (3 AM UTC)
  0 3 * * * /app/backend/scripts/nightly_retrain.sh >> /var/log/levibot/retrain.log 2>&1
  ```

#### 5.3: Model Versioning

- [ ] **Task:** Model artifact tracking
  - [ ] Naming: `ensemble_YYYYMMDD_HHMMSS.pkl`
  - [ ] Metadata: `model_metadata.json`
  ```json
  {
    "version": "20251014_030000",
    "train_date": "2025-10-14T03:00:00Z",
    "backtest_sharpe": 1.78,
    "backtest_win_rate": 0.62,
    "hyperparams": {...}
  }
  ```
  - [ ] Rollback capability (keep last 7 models)

#### 5.4: Retrain Monitoring

- [ ] **Task:** Prometheus metrics
  ```python
  retrain_duration_seconds = Histogram('levibot_retrain_duration_seconds')
  retrain_success_total = Counter('levibot_retrain_success_total')
  retrain_failure_total = Counter('levibot_retrain_failure_total')
  model_sharpe_ratio = Gauge('levibot_model_sharpe_ratio')
  ```

**Epic 5 Test:**

```bash
# Manual retrain trigger
bash backend/scripts/nightly_retrain.sh

# Check model updated
ls -lh ml/models/current.pkl
# Verify symlink points to latest
```

**Epic 5 KPI:**

- Retrain cycle time: <30min
- Success rate: ≥95%
- Model improvement (Sharpe): +10% monthly

---

## 📊 Sprint KPI Dashboard

### Hedef Metrikler

| Metrik                      | Hedef  | Mevcut | Durum |
| --------------------------- | ------ | ------ | ----- |
| **Model Accuracy**          | ≥60%   | TBD    | ⏳    |
| **Engine Uptime**           | ≥99%   | TBD    | ⏳    |
| **Max Drawdown**            | ≤12%   | TBD    | ⏳    |
| **Inference Latency (P95)** | <400ms | TBD    | ⏳    |
| **Retrain Cycle Time**      | <30min | TBD    | ⏳    |
| **Crash Recovery Time**     | <10s   | TBD    | ⏳    |
| **Test Coverage**           | ≥80%   | ~60%   | 🔴    |
| **CI/CD Pipeline Time**     | <10min | TBD    | ⏳    |

---

## 📅 Sprint Timeline (Gantt Chart)

```
Week 1 (14-18 Ekim)
├─ Mon: Epic 1.1-1.2 (Engine manager refactor)
├─ Tue: Epic 1.3-1.4 (Health monitor + crash recovery)
├─ Wed: Epic 1.5 (Logging) + Epic 1 test
├─ Thu: Epic 2.1 (Sentiment extractor)
└─ Fri: Epic 2.2 (OnChain fetcher)

Week 2 (21-25 Ekim)
├─ Mon: Epic 2.3 (Ensemble predictor)
├─ Tue: Epic 2.4 (Auto tuner)
├─ Wed: Epic 2 test + backtesting
├─ Thu: Epic 3.1-3.2 (Risk manager)
└─ Fri: Epic 3.3 (Rebalancer) + Epic 3 test

Week 3 (28-31 Ekim)
├─ Mon: Epic 4.1-4.2 (CI/CD + tests)
├─ Tue: Epic 4.3 (Docker optimization)
├─ Wed: Epic 5.1-5.2 (Nightly retrain)
├─ Thu: Epic 5.3-5.4 (Model versioning + monitoring)
└─ Fri: Sprint review + retrospective
```

---

## 📦 Deliverables (Sprint Output Files)

### Core Files

- `backend/src/engine_manager.py` (Epic 1)
- `backend/data/engine_registry.json` (Epic 1)
- `backend/ml/features/sentiment_extractor.py` (Epic 2)
- `backend/ml/features/onchain_fetcher.py` (Epic 2)
- `backend/ml/models/ensemble_predictor.py` (Epic 2)
- `backend/ml/auto_tuner.py` (Epic 2)
- `backend/risk/manager.py` (Epic 3)
- `backend/risk/policy.yaml` (Epic 3)
- `backend/risk/rebalancer.py` (Epic 3)
- `.github/workflows/deploy.yml` (Epic 4)
- `backend/scripts/nightly_retrain.sh` (Epic 5)

### Documentation

- `sprint/S9_GEMMA_FUSION_PLAN.md` (bu dosya)
- `docs/AI_FUSION_ARCHITECTURE.md` (Epic 2)
- `docs/RISK_MANAGER_V2.md` (Epic 3)
- `docs/CICD_PIPELINE.md` (Epic 4)

### Tests

- `backend/tests/test_ai.py` (Epic 2)
- `backend/tests/test_engine.py` (Epic 1)
- `backend/tests/test_risk.py` (Epic 3)
- `backend/tests/integration/test_clickhouse.py` (Epic 4)

---

## 🧩 Sprint Özeti

> **Sprint-9**, LeviBot'un "tek işlemci bot" kimliğinden çıkıp **çoklu zekâ katmanına sahip, kendi öğrenen sistem** haline dönüşeceği sprint'tir.
>
> Bu aşamadan sonra LeviBot artık:
>
> - ✅ 10-15 sembolu paralel işleyebilen
> - ✅ Fiyat + duygu + zincir verisini birleştiren
> - ✅ Her gece kendi kendini optimize eden
> - ✅ Risk dengesini otomatik sağlayan
> - ✅ Production-grade CI/CD ile deploy edilen
>
> **bir AI Trader platformudur.**

---

## 🔜 Sprint-10 Preview (Kasım 2025)

Sprint-9 tamamlandıktan sonra sırada:

### LeviLang + Dashboard Sprint

- **LeviLang DSL:** YAML tabanlı strateji dili
- **Next.js Dashboard:** Canlı PnL + grafikler
- **Telegram Bot v2:** `/pnl`, `/risk`, `/strategy` komutları
- **Backtesting UI:** Historical replay arayüzü
- **Multi-timeframe:** 5m + 15m + 1h + 4h ensemble

---

## 🏆 Definition of Done (DoD)

Sprint-9 tamamlanmış sayılır eğer:

- [ ] Tüm epic'ler tamamlandı (5/5)
- [ ] Tüm acceptance criteria karşılandı
- [ ] Unit test coverage ≥80%
- [ ] Integration tests passing
- [ ] CI/CD pipeline green
- [ ] Production deployment successful
- [ ] KPI hedefleri karşılandı (6/8)
- [ ] Sprint review yapıldı
- [ ] Retrospective notları dokümante edildi
- [ ] Sprint-10 planning başladı

---

## 🔗 Referanslar

### Planlama Dokümanları

- [PLANNING_INDEX.md](../docs/PLANNING_INDEX.md)
- [DEVELOPMENT_ROADMAP.md](../docs/DEVELOPMENT_ROADMAP.md)
- [SPRINT_PLANNING.md](../docs/SPRINT_PLANNING.md)

### Teknik Dokümanlar

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md)
- [ML_SPRINT3_GUIDE.md](../docs/ML_SPRINT3_GUIDE.md)
- [GO_LIVE_PLAYBOOK.md](../docs/GO_LIVE_PLAYBOOK.md)

---

**Hazırlayan:**  
🤖 _Balkız AI – CTO Asistanı_  
🧔‍♂️ _Onur Mutlu (NovaBaron Protocol)_  
📆 _13 Ekim 2025 — Sprint-9: Gemma Fusion_

---

**Versiyon:** 1.0  
**Son Güncelleme:** 13 Ekim 2025  
**Sonraki Review:** 18 Ekim 2025 (Week 1 checkpoint)

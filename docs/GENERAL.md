# LeviBot — Genel Doküman + Panelden Çalıştırma (Cursor Prompts)

Bu doküman; modüller, veri akışları, API uçları, panel Trace View/raporlar, Telegram komutları ve kopyala-yapıştır çalıştırma prompt’larını (P1–P6) içerir.

## 1) Modüller ve ana fonksiyonlar

- Logger (`backend/src/infra/logger.py`): JSONL event yazımı (saatlik dosyalar: `data/logs/YYYY-MM-DD/events-<HH>.jsonl`). Kısa yol: `log_event(event_type, payload)`.
- Metrics (`backend/src/infra/metrics.py`): Prometheus Gauge/Counter’lar. Uç: `/metrics/prom`.
- DuckDB (`backend/src/infra/duck.py`): `load_day(day)`, `load_week_ending(end)`.
- Archive (`backend/src/infra/archive.py`): Günlük `.zst` sıkıştır + S3 yükle (`archive_day`). GC (`gc_local`).
- Scheduler (`backend/src/app/schedule.py`): `schedule_jobs()` → 03:00 UTC arşiv.
- Risk Guard (`backend/src/risk/guard.py`): `KillSwitch` günlük DD guard’ı; pre-trade check ve realized PnL besleme.
- Precision (`backend/src/exec/precision.py`): price/amount step quantize + minNotional kontrolü.
- Router/OCO (`backend/src/exec/router.py`): ccxt client, `norm_ccxt_symbol`, post-only limit + TWAP fallback, yazılım OCO.
- News LLM (`backend/src/news/rss_ingest.py`, `backend/src/news/llm_scorer.py`, `backend/src/news/cache.py`): RSS çek, cache’li skor (degrade friendly), `NEWS_SCORE` loglar.
- Signals (`backend/src/signals/*.py`): baseline + hybrid, ETH-led tetikleyici (iskelet), trend/ML skorları (`signals/trend.py`, `signals/ml_model.py`).
- Telegram bias/pulse (`backend/src/features/telegram_bias.py`, `backend/src/features/telegram_pulse.py`) → ensemble `signals/hybrid.py`.
- TWAP Adapters: `backend/src/exec/algo_base.py` (registry), `exec/algo_binance.py` (native), `exec/algo_bybit.py` (stub), software TWAP `exec/twap.py`.
- Backtest (`backend/src/backtest/engine.py`): walk-forward stub.

## 2) API uçları ve veri akışları

- Sağlık/Koşu: `GET /status`, `POST /start`, `POST /stop`
- Konfig: `GET /config`, `POST /config/reload`, `PUT /config` (risk override)
- Risk: `POST /risk/leverage`
- Metrikler: `GET /metrics` (JSON), `GET /metrics/prom` (Prometheus)
- Raporlar: `GET /reports/daily?date&format=json|csv|parquet`, `GET /reports/weekly?end&format=json|csv|parquet`
- Olay akışı: `GET /events?trace_id|since_iso&limit&format=json|jsonl`
- Test emir: `POST /exec/test-order` (ccxt testnet smoke)

Veri akışı: API çağrıları ve işlem mantığı kritik anlarda `logger` ile JSONL yazar; `reports` uçları aynı dosyalardan DuckDB ile okur; panel Trace View `/events` ile gösterir; Prometheus metrikleri `/metrics/prom` ile dışa verilir.

## 3) Panel: Trace View ve Raporlar

- Trace View: `trace_id` gir → `GET /events?trace_id=...` → timeline. Export: `format=jsonl`.
- Raporlar: Dashboard/Reports menüsünden Daily/Weekly indir (CSV/Parquet).

## 4) Telegram komutları

- `/start`, `/stop`, `/status`, `/set leverage 3`
- ENV: `LEVI_TELEGRAM_BOT_TOKEN`, `LEVI_API_BASE`.

## 5) Cursor Prompts (P1–P6)

Aşağıdaki blokları sırayla kopyala-çalıştır.

### P1 — Python ortamı ve bağımlılıklar
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
# testnet için ek: pip install ccxt apscheduler boto3 zstandard duckdb pandas scikit-learn joblib
```

### P2 — ENV ve Config
```bash
cp docs/ENV.md .env  # içeriğini düzenle: EXCHANGE=bybit|binance, NETWORK=testnet|mainnet, API KEY/SECRET, REDIS_URL...
# Configler: backend/configs/users.yaml, risk.yaml, symbols.yaml, features.yaml, model.yaml, strategy.yaml kontrol et
```

### P3 — Backend API’yi başlat
```bash
cd backend
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### P4 — Panel ve Telegram
```bash
cd frontend/panel && npm i && npm run dev &
cd -
cd telegram && python -m bot &
```

### P5 — Smoke: HTTP ve Export’lar
```bash
# Durum ve konfig
curl -s http://localhost:8000/status | jq
curl -s http://localhost:8000/config | jq
# Başlat & risk override
curl -s -X POST http://localhost:8000/start | jq
curl -s -X PUT http://localhost:8000/config -H "Content-Type: application/json" -d '{"max_leverage":3}' | jq
# Events ve export
curl -s "http://localhost:8000/events?since_iso=$(date -u +%Y-%m-%dT%H:%M:%SZ)&limit=5" | jq
curl -s -D- -o daily.csv "http://localhost:8000/reports/daily?format=csv"
curl -s -D- -o weekly.parquet "http://localhost:8000/reports/weekly?format=parquet"
```

### P6 — ccxt Testnet emir + OCO smoke
```bash
# Markets
python -c "import ccxt; ex=ccxt.bybit(); ex.set_sandbox_mode(True); print('markets', len(ex.load_markets()))"
# Test emir
curl -s -X POST "http://localhost:8000/exec/test-order" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"ETHUSDT","side":"buy","notional_usd":25}' | jq
# Metrikler
curl -s http://localhost:8000/metrics/prom | grep -E "levibot_equity|levibot_open_positions|levibot_orders_total"
```

## 6) Runbook notları

- Post-only reddi durumunda TWAP fallback loglanır (ORDER_NEW notunda `twap_parts`).
- Precision/minNotional hatası için `notional_usd`’yi 25–50 aralığına çek.
- Kill-switch tetiklenirse pre-trade check 400/409 ile bloklar ve `KILL_SWITCH` event’i düşer.
- Archive: bir gün sonra 03:00 UTC’de `.zst` + `manifest.json` S3’e.

## 7) Opsiyonel ekler

- ETH-led altseason tetikleyici formül dokümanı
- Walk-forward backtest rehberi (purged k-fold + WFO)
- TWAP Adapters: Binance native + Bybit stub; registry (`exec/algo_base.py`) ile otomatik seçim.
- ML Eğitim: `backend/scripts/train_wf_calibrated.py` ile kalibre model; inference `signals/ml_model.py`.



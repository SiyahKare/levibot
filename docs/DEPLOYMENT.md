# LeviBot — Deployment Guide

> Production-ready compose: redis + api + panel + nginx (+ optional minio)

## 0) Quick Start (Prod Compose)

```bash
cp .env.prod.example .env.prod
# Zorunlu: API_KEYS=key1,key2
# Opsiyonel: ZEROX_API_KEY, RESERVOIR_API_KEY, ETH_HTTP, TELEGRAM_*
make prod-up

# Health
curl -s http://localhost/healthz | jq
curl -s http://localhost/readyz | jq

# Panel
open http://localhost

# API Smoke
curl -H "X-API-Key: key1" -s "http://localhost/signals/score?text=BUY%20BTCUSDT" | jq
```

## 1) Services

* **redis**: distributed rate limit + future caching
* **api**: FastAPI (uvicorn), Prometheus metrics, health endpoints
* **panel**: build ci/CD (static files), Nginx ile servis edilir
* **nginx**: reverse proxy
  * `/` → panel static
  * `/metrics/prom|/healthz|/readyz|/api routes` → API
* **minio** (opsiyonel): local S3 (dev/demo)

## 2) ENV (seçmece)

* **Security**: `API_KEYS`, `SECURED_PATH_PREFIXES` (default: /signals,/exec,/paper,/risk)
* **Rate Limit**: `REDIS_URL`, `RL_WINDOW_SEC`, `RL_MAX`, `RL_BURST`
* **Autoroute**: `AUTO_ROUTE_ENABLED`, `AUTO_ROUTE_DRY_RUN`, `AUTO_ROUTE_MIN_CONF`, `AUTO_ROUTE_SYMBOL_MAP`, `AUTO_ROUTE_DEFAULT_NOTIONAL`
* **Risk**: `RISK_DEFAULT_POLICY`, `RISK_NOTIONAL_MIN/MAX`
* **Build Info**: `BUILD_VERSION`, `BUILD_SHA`, `BUILD_BRANCH`
* **S3/MinIO**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_LOG_BUCKET`, `AWS_ENDPOINT_URL`
* **Telegram**: `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, `TELEGRAM_CHANNELS`, `TELEGRAM_CHANNEL_TRUST`

> Tam liste için `.env.prod.example` ve `ENV.example`'a bak.

## 3) Health & Observability

* **Liveness**: `GET /livez` → `{ok:true}`
* **Readiness**: `GET /readyz` → eth RPC varsa gerçek kontrol
* **Metrics**: `GET /metrics/prom`
  * `levibot_build_info{version,git_sha,branch} 1`
  * `levibot_http_requests_total{path,method,status}`
  * `levibot_events_total{event_type}`
* **Dashboards/Alerts**: `ops/prometheus/*.yml`, `ops/grafana/dashboards/*.json`

## 4) Logs & Archival

* **Local JSONL**: `backend/data/logs/YYYY-MM-DD/events-*.jsonl`
* **Archiver**: `ops/s3_archiver.py` + `ops/cron/archive.sh`
  * compress → `.gz`
  * upload → S3/MinIO (bucket: `${S3_LOG_BUCKET}`)
  * prune → `keep_days`
* **Docker job**: `ops/docker-compose-cron.yml` (retrain + archive)

## 5) Security Notes

* **API Keys**: production'da zorunlu; Nginx iptables ile sınırlandırılabilir
* **Rate limit**: Redis token bucket; burst toleransı
* **PII Mask**: logger mask aktif
* **Secrets**: `.env` yerine vault seviyesi önerilir (HashiCorp/AWS Secrets)

## 6) Scaling

* **Horizontally scale API**: multiple replicas + shared Redis RL
* **Panel**: statik, çok hafif
* **Model**: cold-start warmup (lifespan'da), retrain cron
* **Storage**: S3/MinIO, lifecycle policies

## 7) Common Pitfalls

* `403` → `X-API-Key` eksik/yanlış
* `429` → rate limit; `RL_MAX`/`RL_WINDOW_SEC` ayarla
* Panel CORS → Nginx reverse route; relative path kullan
* Readiness `ok=false` → `ETH_HTTP` cevap vermiyor
* E2E flake → dry-run açık, mocks aktif; test komutlarını kullan

## 8) One-liners

```bash
# Prod stack
make prod-up && make prod-ps
make prod-logs
make prod-down

# MinIO (dev only)
make minio-up && make archive-minio

# Tests
make test
make e2e
make test-all
```

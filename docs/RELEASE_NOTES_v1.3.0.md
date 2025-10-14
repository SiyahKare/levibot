# 🚀 LeviBot v1.3.0 — Build Info, MinIO, Lifespan

**Date:** October 2025  
**Codename:** Sprint 6 (Observability++ & Runtime)

## ✨ Highlights
- **Build Info Metrics (PR-26):** `levibot_build_info{version,git_sha,branch} 1`
- **MinIO Local Stack (PR-27):** S3-compatible local storage for dev/demo
- **Lifespan Handlers (PR-28):** Modern FastAPI `lifespan` startup/shutdown; deprecation warnings gone

## 🔧 What's New

### PR-26: Build Info Metrics
- `backend/src/infra/version.py`: ENV-fallback version reader (git command + ENV + default)
- `backend/src/infra/metrics.py`: `levibot_build_info` Prometheus gauge with labels
- `backend/src/app/main.py`: Set build_info on startup
- `ops/api.Dockerfile`: BUILD_VERSION, BUILD_SHA, BUILD_BRANCH args
- `.env.prod.example`: BUILD_* env template
- `backend/tests/test_version_metric.py`: 6 unit tests (all passed)
- **Example:** `levibot_build_info{version="1.3.0",git_sha="34f3c80",branch="main"} 1.0`

### PR-27: MinIO Local Stack
- `ops/minio-compose.yml`: MinIO server + mc (bucket bootstrap)
- `.env.prod.example`: MinIO env template (credentials + endpoint)
- `Makefile`: `minio-up`, `minio-down`, `minio-logs`, `archive-minio`
- **Features:**
  - S3-compatible local storage (no AWS account needed)
  - Auto bucket creation (`levibot-logs`)
  - Web console: http://localhost:9001 (minioadmin/minioadmin)
  - S3 API: http://localhost:9000
  - Archiver integration: `AWS_ENDPOINT_URL` support

### PR-28: Lifespan Handlers
- `backend/src/app/main.py`: `@on_event("startup")` → `lifespan` context manager
- `backend/src/ml/signal_model.py`: `warmup()` helper (idempotent model cache)
- `backend/tests/test_lifespan_smoke.py`: 2 smoke tests (healthz + build_info metric)
- **Benefits:**
  - Modern FastAPI pattern (0.109.0+)
  - Graceful startup/shutdown hooks
  - Build info metric set on startup
  - Model warmup (idempotent cache)
  - Zero breaking changes
  - Deprecation warnings eliminated

## 🧪 Tests
- **6 unit tests** (build info) → ✅
- **2 smoke tests** (lifespan) → ✅
- **E2E tests** (from v1.2.0) remain green
- **Total:** 46+ tests passing

## 🧭 Quick Start

### Production Stack
```bash
cp .env.prod.example .env.prod
make prod-up
open http://localhost
curl -s http://localhost/metrics/prom | grep levibot_build_info
```

### MinIO (Local S3)
```bash
make minio-up
# Console: http://localhost:9001 (minioadmin/minioadmin)

# Test archiver with MinIO
make archive-minio

# Stop MinIO
make minio-down
```

### Build Info Metric
```bash
curl -s http://127.0.0.1:8000/metrics/prom | grep levibot_build_info
# → levibot_build_info{version="1.3.0",git_sha="34f3c80",branch="main"} 1.0
```

## ⚠️ Notes

- **MinIO credentials:** Default creds (minioadmin/minioadmin) are for local only; change in production
- **Risk policy:** On restart, falls back to ENV (use `/risk/policy` to switch at runtime)
- **Deprecation warnings:** All FastAPI deprecation warnings eliminated with lifespan pattern

## 📊 Stats

- **3 PRs** (PR-26, PR-27, PR-28)
- **20+ files changed**
- **+290 lines added**
- **8 new tests**
- **Zero breaking changes**

## 🔗 Links

- **v1.2.0:** [S3 Archiver + E2E Tests](RELEASE_NOTES_v1.2.0.md)
- **v1.1.0:** [Redis RL + Charts + Prod Compose](RELEASE_NOTES_v1.1.0.md)
- **v1.0.0:** [Core AI + Risk + Panel + Docker](RELEASE_NOTES_v1.0.0.md)

## 🎯 Next Milestone

- **v1.4.0:** GitHub Issue/PR templates + Architecture docs + Performance benchmarks

---

**Full Changelog:** https://github.com/SiyahKare/levibot/compare/v1.2.0...v1.3.0

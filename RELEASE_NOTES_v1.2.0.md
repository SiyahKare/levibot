# 🚀 LeviBot v1.2.0 — S3 Archiver + E2E Tests

**Date:** October 2025

## What's New

### PR-24: S3 Log Archiver
- **JSONL → `.gz` compress**: Automatic daily log compression with gzip
- **S3 multipart upload**: boto3-powered upload with MinIO compatibility
- **Auto-prune**: Configurable `keep_days` parameter for disk hygiene
- **Cron + Docker job**: Production-ready scheduling with `ops/cron/archive.sh`
- **Make targets**: `archive-run`, `archive-dry`, `archive-docker`
- **ENV config**: `S3_LOG_BUCKET`, `AWS_*`, `ARCHIVE_KEEP_DAYS`

### PR-25: E2E httpx Tests
- **Live uvicorn server**: Real HTTP server testing (not TestClient)
- **End-to-end scenarios**: `/signals/score`, ingest → events chain validation
- **JSONL verification**: Event chain proof in actual log files
- **CEX paper offline fallback**: Deterministic paper order testing
- **Fast execution**: ~9s for 3 comprehensive tests
- **CI integration**: Optional E2E stage with `-m e2e` marker
- **Make targets**: `e2e`, `test-all`

## Quick Start

```bash
# Production Docker Stack
cp .env.prod.example .env.prod
make prod-up
open http://localhost

# E2E Tests (Local)
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
make e2e

# S3 Archiver (Ops)
make archive-dry  # dry-run
docker compose -f ops/docker-compose-cron.yml run --rm archive  # real upload
```

## Stats

- **3 new E2E tests** (total: 38+ tests)
- **Ops hygiene**: Automated archival + disk cleanup
- **Demo/Prod parity**: Enhanced production readiness
- **Zero external dependencies**: Offline-safe E2E tests

## Technical Highlights

### S3 Archiver
- **Compression ratio**: ~70-80% size reduction (JSONL → .gz)
- **Multipart upload**: Automatic for large files (boto3)
- **Idempotent**: Same day = overwrite (S3 versioning compatible)
- **MinIO support**: `AWS_ENDPOINT_URL` for S3-compatible storage
- **Graceful dry-run**: Test mode without upload/delete

### E2E Tests
- **Real server**: Uvicorn with random free port
- **ENV isolation**: Temporary log directory + test-specific config
- **DRY_RUN autoroute**: Safe paper order validation
- **Event verification**: JSONL grep for actual event chain
- **Low flake**: Offline fallbacks + fixed seed + retry logic

## Breaking Changes

None. Fully backward compatible.

## Upgrade Notes

1. **S3 Archiver** (optional):
   - Add `boto3>=1.34.0` to requirements (already in `requirements.txt`)
   - Configure ENV: `S3_LOG_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - Test with `make archive-dry`

2. **E2E Tests** (optional):
   - Add `httpx>=0.27.0` to requirements (already in `requirements.txt`)
   - Run with `make e2e`
   - CI: Set `E2E=true` env var to enable E2E stage

## Known Issues

- Deprecation warnings for `datetime.utcnow()` (Python 3.13+) — non-blocking
- FastAPI `on_event` deprecation — will migrate to lifespan handlers in v1.3.0

## Contributors

- @onur (all PRs)

## Full Changelog

**PR-24 (S3 Archiver)**:
- `backend/src/ops/s3_archiver.py`: Compress + upload + prune logic
- `ops/cron/archive.sh`: Executable cron script
- `ops/docker-compose-cron.yml`: Archive service
- `backend/requirements.txt`: boto3 dependency
- `.env.prod.example`: S3 ENV template
- `Makefile`: archive targets

**PR-25 (E2E Tests)**:
- `backend/tests/e2e/conftest.py`: Uvicorn test server fixture
- `backend/tests/e2e/test_signals_flow.py`: Signals + events tests
- `backend/tests/e2e/test_paper_order_path.py`: Paper order tests
- `backend/requirements.txt`: httpx dependency
- `pytest.ini`: e2e marker
- `Makefile`: e2e targets
- `.github/workflows/ci.yml`: Optional E2E stage

**Docs**:
- `README.md`: Quick Start (Docker), E2E, S3 Archiver, Release Matrix

---

**Previous releases:**
- [v1.1.0](RELEASE_NOTES_v1.1.0.md) — Redis RL + Charts + Prod Compose
- [v1.0.0](RELEASE_NOTES_v1.0.0.md) — Core AI + Risk + Panel + Docker

**Next milestone:**
- v1.3.0: Build Info Metrics + Lifespan Handlers + MinIO Local Stack

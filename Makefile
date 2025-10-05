.PHONY: run test e2e test-all logs live-tg prod-up prod-logs prod-down prod-ps archive-run archive-dry archive-docker minio-up minio-down minio-logs archive-minio perf perf-save perf-compare fmt lint clean fix-frontend

VENV=.venv

run:
	$(VENV)/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV)/bin/python -m pytest -q --ignore=backend/tests/e2e

e2e:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV)/bin/python -m pytest backend/tests/e2e -m e2e -q

test-all:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV)/bin/python -m pytest -q

logs:
	@ls -1 backend/data/logs/*/events-*.jsonl 2>/dev/null || echo "no logs yet"

live-tg:
	$(VENV)/bin/python -m backend.src.ingest.telegram_live

# Production Docker Compose targets
prod-up:
	docker compose -f docker-compose.prod.yml up --build -d

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f --tail=200

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-ps:
	docker compose -f docker-compose.prod.yml ps

# S3 Archiver targets
archive-run:
	$(VENV)/bin/python -m backend.src.ops.s3_archiver

archive-dry:
	ARCHIVE_DRY_RUN=true $(VENV)/bin/python -m backend.src.ops.s3_archiver

archive-docker:
	docker compose -f ops/docker-compose-cron.yml run --rm archive

# MinIO (local S3-compatible)
minio-up:
	docker compose -f ops/minio-compose.yml up -d

minio-down:
	docker compose -f ops/minio-compose.yml down -v

minio-logs:
	docker compose -f ops/minio-compose.yml logs -f --tail=200

archive-minio:
	AWS_ENDPOINT_URL=http://localhost:9000 \
	AWS_ACCESS_KEY_ID=$${AWS_ACCESS_KEY_ID:-minioadmin} \
	AWS_SECRET_ACCESS_KEY=$${AWS_SECRET_ACCESS_KEY:-minioadmin} \
	AWS_REGION=$${AWS_REGION:-us-east-1} \
	S3_LOG_BUCKET=$${S3_LOG_BUCKET:-levibot-logs} \
	$(VENV)/bin/python -m backend.src.ops.s3_archiver

# Performance benchmarks
perf:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV)/bin/pytest backend/tests/test_performance.py --benchmark-only -q

perf-save:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV)/bin/pytest backend/tests/test_performance.py --benchmark-only --benchmark-save=$${BENCH_NAME:-baseline-$(shell date +%Y%m%d)} -q

perf-compare:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV)/bin/pytest backend/tests/test_performance.py --benchmark-only --benchmark-compare=$${BENCH_BASE:-baseline-v1.3} -q

# Developer experience helpers
fmt:
	@echo "→ Python format (black) + imports (ruff)…"
	$(VENV)/bin/python -m black backend || true
	$(VENV)/bin/ruff check backend --select I --fix || true

lint:
	@echo "→ Python lint (ruff)…"
	$(VENV)/bin/ruff check backend
	@echo "→ Frontend lint (eslint)…"
	cd frontend/panel && npm run -s lint || echo "hint: run 'npm i' in frontend/panel"

clean:
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} \; 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -prune -exec rm -rf {} \; 2>/dev/null || true
	@rm -rf backend/artifacts/*.tmp 2>/dev/null || true

fix-frontend:
	cd frontend/panel && npm run -s fmt || npx prettier -w "src/**/*.{ts,tsx,js,jsx,json,css,md}"
	cd frontend/panel && npm run -s lint -- --fix || true



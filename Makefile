.PHONY: run test logs live-tg prod-up prod-logs prod-down prod-ps archive-run archive-dry archive-docker

VENV=.venv

run:
	$(VENV)/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload

test:
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



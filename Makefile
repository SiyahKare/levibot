.PHONY: run test logs live-tg

VENV=.venv

run:
	$(VENV)/bin/uvicorn backend.src.app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV)/bin/python -m pytest -q

logs:
	@ls -1 backend/data/logs/*/events-*.jsonl 2>/dev/null || echo "no logs yet"

live-tg:
	$(VENV)/bin/python -m backend.src.ingest.telegram_live



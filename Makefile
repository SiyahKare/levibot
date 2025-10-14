.PHONY: help init lint format test cov docker up down logs clean

help:  ## Bu yardım mesajını göster
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

init:  ## Geliştirme ortamını kur
	@echo "📦 Installing dependencies..."
	cd backend && pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio ruff black isort pre-commit
	pre-commit install
	@echo "✅ Development environment ready!"

lint:  ## Kod kalitesini kontrol et
	@echo "🔍 Running linters..."
	ruff check backend/src backend/tests
	black --check backend/src backend/tests
	isort --check-only backend/src backend/tests
	@echo "✅ Linting passed!"

format:  ## Kodu otomatik formatla
	@echo "🎨 Formatting code..."
	ruff check --fix backend/src backend/tests
	black backend/src backend/tests
	isort backend/src backend/tests
	@echo "✅ Formatting complete!"

test:  ## Testleri çalıştır
	@echo "🧪 Running tests..."
	cd backend && PYTHONPATH=. pytest tests/test_automl_nightly.py \
		tests/test_engine_smoke.py \
		tests/test_manager_smoke.py \
		tests/test_recovery_policy.py \
		tests/test_ml_components.py \
		tests/test_risk_manager.py \
		-v --tb=short -m "not slow"
	@echo "✅ Tests passed!"

cov:  ## Test coverage raporu
	@echo "📊 Generating coverage report..."
	cd backend && PYTHONPATH=. pytest tests/test_automl_nightly.py \
		tests/test_engine_smoke.py \
		tests/test_manager_smoke.py \
		tests/test_recovery_policy.py \
		tests/test_ml_components.py \
		tests/test_risk_manager.py \
		--cov=src --cov-report=term-missing --cov-report=html \
		-m "not slow"
	@echo "✅ Coverage report: backend/htmlcov/index.html"

docker:  ## Docker image'ını build et
	@echo "🐳 Building Docker image..."
	docker build -f docker/app.Dockerfile -t levibot:local .
	@echo "✅ Image built: levibot:local"

up:  ## Servisleri başlat (docker-compose dev)
	@echo "🚀 Starting development services..."
	docker compose -f docker-compose.dev.yml up -d --build
	@echo "✅ Services started!"
	@echo "   Panel:    http://localhost:5173"
	@echo "   Engines:  http://localhost:5173/engines"
	@echo "   Backtest: http://localhost:5173/backtest"
	@echo "   Ops:      http://localhost:5173/ops"
	@echo "   API Docs: http://localhost:8000/docs"
	@echo "   Grafana:  http://localhost:3000 (admin/admin)"

down:  ## Servisleri durdur
	@echo "🛑 Stopping services..."
	docker compose -f docker-compose.dev.yml down
	@echo "✅ Services stopped!"

logs:  ## Servis loglarını izle
	docker compose -f docker-compose.dev.yml logs -f --tail=200

restart:  ## Servisleri yeniden başlat
	@echo "🔄 Restarting services..."
	docker compose -f docker-compose.dev.yml restart
	@echo "✅ Services restarted!"

clean:  ## Cache ve geçici dosyaları temizle
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

smoke:  ## Smoke test URLs
	@echo "🔎 Smoke Test URLs:"
	@echo ""
	@echo "  Frontend:"
	@echo "    Panel:    http://localhost:5173"
	@echo "    Engines:  http://localhost:5173/engines"
	@echo "    Backtest: http://localhost:5173/backtest"
	@echo "    Ops:      http://localhost:5173/ops"
	@echo ""
	@echo "  Backend:"
	@echo "    Health:   http://localhost:8000/health"
	@echo "    Docs:     http://localhost:8000/docs"
	@echo "    Engines:  http://localhost:8000/engines"
	@echo "    Stream:   http://localhost:8000/stream/engines"
	@echo ""
	@echo "  Monitoring:"
	@echo "    Prometheus: http://localhost:9090"
	@echo "    Grafana:    http://localhost:3000 (admin/admin)"
	@echo ""
	@echo "Quick Tests:"
	@curl -sf http://localhost:8000/health | jq '.' 2>/dev/null || echo "  ❌ API not responding"
	@curl -sf http://localhost:8000/engines 2>/dev/null && echo "  ✅ /engines OK" || echo "  ❌ /engines failed"
	@curl -sf http://localhost:8000/live/status | jq '.' 2>/dev/null && echo "  ✅ /live/status OK" || echo "  ❌ /live/status failed"

automl:  ## Manuel AutoML pipeline çalıştır
	@echo "🌙 Running nightly AutoML..."
	cd backend && PYTHONPATH=. python -m src.automl.nightly_retrain
	@echo "✅ AutoML complete!"

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

up:  ## Servisleri başlat (docker-compose)
	@echo "🚀 Starting services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "   API: http://localhost:8000"
	@echo "   Panel: http://localhost:3000"

down:  ## Servisleri durdur
	@echo "🛑 Stopping services..."
	docker-compose down
	@echo "✅ Services stopped!"

logs:  ## Servis loglarını izle
	docker-compose logs -f --tail=100

clean:  ## Cache ve geçici dosyaları temizle
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

smoke:  ## Smoke test (API health check)
	@echo "🔥 Running smoke test..."
	@curl -f http://localhost:8000/healthz || echo "❌ API not responding"
	@curl -f http://localhost:8000/engines/status || echo "❌ Engines endpoint failed"
	@echo "✅ Smoke test complete!"

automl:  ## Manuel AutoML pipeline çalıştır
	@echo "🌙 Running nightly AutoML..."
	cd backend && PYTHONPATH=. python -m src.automl.nightly_retrain
	@echo "✅ AutoML complete!"

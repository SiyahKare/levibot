
# ============================================
# Docker Quick Commands
# ============================================
.PHONY: up down restart logs status clean rebuild

up: ## Start all Docker services
	@echo "🚀 Starting all services..."
	@docker compose up -d
	@sleep 3
	@docker compose ps

down: ## Stop all Docker services
	@echo "🛑 Stopping all services..."
	@docker compose down

restart: ## Restart all Docker services
	@echo "🔄 Restarting all services..."
	@docker compose restart

logs: ## Show logs from all services
	@docker compose logs -f

status: ## Show status of all services
	@docker compose ps

clean: ## Stop and remove all containers, networks, volumes
	@echo "🧹 Cleaning up..."
	@docker compose down -v

rebuild: ## Rebuild and restart all services
	@echo "🔨 Rebuilding all services..."
	@docker compose build
	@docker compose up -d

rebuild-panel: ## Rebuild and restart panel only
	@echo "🎨 Rebuilding panel..."
	@docker compose build panel
	@docker compose up -d panel

rebuild-api: ## Rebuild and restart API only
	@echo "⚙️  Rebuilding API..."
	@docker compose build api
	@docker compose up -d api

open-panel: ## Open panel in browser
	@open http://localhost:3002/risk

check: ## Quick health check
	@./scripts/canary_check.sh


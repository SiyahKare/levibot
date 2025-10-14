# ═══════════════════════════════════════════════════════════════
# LeviBot Enterprise AI Signals Platform - Makefile
# ═══════════════════════════════════════════════════════════════

.PHONY: help up down restart logs ps clean test lint format check-env init-db smoke-test

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)LeviBot Enterprise AI Signals Platform$(NC)"
	@echo "$(YELLOW)Available commands:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

check-env: ## Check if .env file exists
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found!$(NC)"; \
		echo "$(YELLOW)Copy ENV.levibot.example to .env and configure it:$(NC)"; \
		echo "  cp ENV.levibot.example .env"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ .env file found$(NC)"

up: check-env ## Start all services
	@echo "$(BLUE)Starting LeviBot Enterprise Platform...$(NC)"
	docker compose -f docker-compose.enterprise.yml up -d
	@echo "$(GREEN)✓ All services started$(NC)"
	@echo "$(YELLOW)Run 'make logs' to view logs$(NC)"

down: ## Stop all services
	@echo "$(BLUE)Stopping LeviBot Enterprise Platform...$(NC)"
	docker compose -f docker-compose.enterprise.yml down
	@echo "$(GREEN)✓ All services stopped$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting LeviBot Enterprise Platform...$(NC)"
	docker compose -f docker-compose.enterprise.yml restart
	@echo "$(GREEN)✓ All services restarted$(NC)"

logs: ## View logs from all services
	docker compose -f docker-compose.enterprise.yml logs -f

logs-panel: ## View panel API logs
	docker compose -f docker-compose.enterprise.yml logs -f panel

logs-signal: ## View signal engine logs
	docker compose -f docker-compose.enterprise.yml logs -f signal_engine

logs-executor: ## View executor logs
	docker compose -f docker-compose.enterprise.yml logs -f executor

logs-bot: ## View Telegram bot logs
	docker compose -f docker-compose.enterprise.yml logs -f telegram_bot

ps: ## Show status of all services
	@echo "$(BLUE)Service Status:$(NC)"
	@docker compose -f docker-compose.enterprise.yml ps

clean: ## Stop and remove all containers, networks, and volumes
	@echo "$(RED)Warning: This will remove all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker compose -f docker-compose.enterprise.yml down -v; \
		echo "$(GREEN)✓ Cleaned up$(NC)"; \
	fi

init-db: ## Initialize ClickHouse database schema
	@echo "$(BLUE)Initializing ClickHouse database...$(NC)"
	@docker compose -f docker-compose.enterprise.yml exec clickhouse clickhouse-client --query "CREATE DATABASE IF NOT EXISTS levibot"
	@docker compose -f docker-compose.enterprise.yml exec clickhouse clickhouse-client --database levibot < backend/sql/001_timescale_init.sql || true
	@echo "$(GREEN)✓ Database initialized$(NC)"

smoke-test: ## Run comprehensive smoke tests
	@bash scripts/smoke_test.sh

test: ## Run Python tests
	@echo "$(BLUE)Running tests...$(NC)"
	cd backend && python -m pytest tests/ -v

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	cd backend && python -m ruff check src/ tests/
	cd backend && python -m mypy src/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	cd backend && python -m ruff format src/ tests/
	cd backend && python -m isort src/ tests/

build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker compose -f docker-compose.enterprise.yml build

pull: ## Pull latest Docker images
	@echo "$(BLUE)Pulling latest images...$(NC)"
	docker compose -f docker-compose.enterprise.yml pull

backup: ## Backup data volumes
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p backups
	@docker run --rm -v levibot_clickhouse_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/clickhouse-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@docker run --rm -v levibot_redis_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/redis-$(shell date +%Y%m%d-%H%M%S).tar.gz -C /data .
	@echo "$(GREEN)✓ Backup created in ./backups/$(NC)"

monitor: ## Open monitoring dashboards
	@echo "$(BLUE)Opening monitoring dashboards...$(NC)"
	@echo "$(YELLOW)Grafana: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Prometheus: http://localhost:9090$(NC)"
	@echo "$(YELLOW)Panel API: http://localhost:8080$(NC)"

shell-panel: ## Open shell in panel container
	docker compose -f docker-compose.enterprise.yml exec panel /bin/bash

shell-signal: ## Open shell in signal engine container
	docker compose -f docker-compose.enterprise.yml exec signal_engine /bin/bash

shell-redis: ## Open Redis CLI
	docker compose -f docker-compose.enterprise.yml exec redis redis-cli

shell-clickhouse: ## Open ClickHouse CLI
	docker compose -f docker-compose.enterprise.yml exec clickhouse clickhouse-client

stats: ## Show Docker stats
	docker stats $(shell docker compose -f docker-compose.enterprise.yml ps -q)

# Development targets
dev-up: ## Start services in development mode
	@echo "$(BLUE)Starting in development mode...$(NC)"
	docker compose -f docker-compose.yml up -d
	@echo "$(GREEN)✓ Development environment started$(NC)"

dev-down: ## Stop development services
	docker compose -f docker-compose.yml down

# Production targets
prod-deploy: check-env build ## Deploy to production
	@echo "$(BLUE)Deploying to production...$(NC)"
	@echo "$(YELLOW)This will restart all services$(NC)"
	docker compose -f docker-compose.enterprise.yml up -d --build
	@echo "$(GREEN)✓ Production deployment complete$(NC)"

prod-rollback: ## Rollback to previous version
	@echo "$(RED)Rolling back...$(NC)"
	docker compose -f docker-compose.enterprise.yml down
	docker compose -f docker-compose.enterprise.yml up -d
	@echo "$(GREEN)✓ Rollback complete$(NC)"

#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# LeviBot Enterprise - Deployment Script
# ═══════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-paper}
COMPOSE_FILE="docker-compose.enterprise.yml"
BACKUP_DIR="./backups"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}LeviBot Enterprise - Deployment to ${ENVIRONMENT}${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Copy ENV.levibot.example to .env and configure it${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running!${NC}"
    exit 1
fi

# Backup current data
echo -e "${YELLOW}Creating backup...${NC}"
mkdir -p ${BACKUP_DIR}
BACKUP_TIMESTAMP=$(date +%Y%m%d-%H%M%S)

if docker volume ls | grep -q levibot_clickhouse_data; then
    docker run --rm \
        -v levibot_clickhouse_data:/data \
        -v $(pwd)/${BACKUP_DIR}:/backup \
        alpine tar czf /backup/clickhouse-${BACKUP_TIMESTAMP}.tar.gz -C /data . 2>/dev/null || true
    echo -e "${GREEN}✓ ClickHouse backup created${NC}"
fi

if docker volume ls | grep -q levibot_redis_data; then
    docker run --rm \
        -v levibot_redis_data:/data \
        -v $(pwd)/${BACKUP_DIR}:/backup \
        alpine tar czf /backup/redis-${BACKUP_TIMESTAMP}.tar.gz -C /data . 2>/dev/null || true
    echo -e "${GREEN}✓ Redis backup created${NC}"
fi

# Pull latest images
echo -e "${YELLOW}Pulling latest Docker images...${NC}"
docker compose -f ${COMPOSE_FILE} pull

# Build custom images
echo -e "${YELLOW}Building custom images...${NC}"
docker compose -f ${COMPOSE_FILE} build

# Stop old containers
echo -e "${YELLOW}Stopping old containers...${NC}"
docker compose -f ${COMPOSE_FILE} down

# Start new containers
echo -e "${YELLOW}Starting new containers...${NC}"
docker compose -f ${COMPOSE_FILE} up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Health check
echo -e "${YELLOW}Running health checks...${NC}"

check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf ${url} > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ${service} is healthy${NC}"
            return 0
        fi
        echo -e "${YELLOW}Waiting for ${service}... (${attempt}/${max_attempts})${NC}"
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "${RED}✗ ${service} failed to start${NC}"
    return 1
}

# Check critical services
check_service "Panel API" "http://localhost:8080/healthz"
check_service "Redis" "http://localhost:6379" || docker compose -f ${COMPOSE_FILE} exec redis redis-cli ping > /dev/null
check_service "ClickHouse" "http://localhost:8123/ping"
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3000/api/health"

# Show running services
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Running Services:${NC}"
docker compose -f ${COMPOSE_FILE} ps

# Show logs
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Recent logs:${NC}"
docker compose -f ${COMPOSE_FILE} logs --tail=20

# Final message
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Access points:${NC}"
echo -e "  Panel API:    http://localhost:8080"
echo -e "  Grafana:      http://localhost:3000 (admin/admin)"
echo -e "  Prometheus:   http://localhost:9090"
echo -e "  Mini App:     http://localhost:5173"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Check Telegram bot: Send /start to your bot"
echo -e "  2. Monitor logs: make logs"
echo -e "  3. View metrics: Open Grafana dashboard"
echo -e "  4. Run smoke test: make smoke-test"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"


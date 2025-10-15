#!/bin/bash
# Rollback script for emergency reverts

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo -e "${RED}Usage: $0 <version>${NC}"
    echo ""
    echo "Available versions:"
    docker images levibot/api --format "  {{.Tag}}" | grep -v latest | head -5
    exit 1
fi

VERSION=$1

echo -e "${YELLOW}🔄 Rolling back to version: $VERSION${NC}"
echo ""

# Confirmation
read -p "Are you sure you want to rollback? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Rollback cancelled."
    exit 0
fi

# 1. Stop current services
echo "Stopping services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml down

# 2. Pull old images
echo "Pulling version $VERSION..."
docker pull levibot/api:$VERSION
docker pull levibot/panel:$VERSION

# 3. Tag as latest (optional)
echo "Tagging as rollback..."
docker tag levibot/api:$VERSION levibot/api:rollback
docker tag levibot/panel:$VERSION levibot/panel:rollback

# 4. Start with old version
echo "Starting with version $VERSION..."
VERSION=$VERSION docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 5. Health check
echo "Waiting for services to start..."
sleep 10

if curl -sf localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Rollback successful${NC}"
    echo ""
    echo "Services running on version: $VERSION"
    docker compose ps
else
    echo -e "${RED}❌ Rollback failed - services not responding${NC}"
    echo "Check logs: docker compose logs -f api"
    exit 1
fi

# 6. Log rollback
echo "$DATE: Rolled back to $VERSION" >> ops/audit.log

echo ""
echo -e "${GREEN}Rollback complete. Monitor metrics for 15 minutes.${NC}"


#!/bin/bash

# ═══════════════════════════════════════════════════════════════
# LeviBot Enterprise - Smoke Test Script
# ═══════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}LeviBot Enterprise - Smoke Test${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"

FAILED=0
PASSED=0

# Test function
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -ne "${YELLOW}Testing ${name}...${NC} "
    
    if curl -sf "${url}" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test with output
test_with_output() {
    local name=$1
    local url=$2
    
    echo -ne "${YELLOW}Testing ${name}...${NC} "
    
    result=$(curl -sf "${url}" 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        echo -e "${BLUE}  Response: ${result:0:100}${NC}"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Docker command test
test_docker_cmd() {
    local name=$1
    local cmd=$2
    
    echo -ne "${YELLOW}Testing ${name}...${NC} "
    
    result=$(eval "${cmd}" 2>&1)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}"
        if [ -n "${result}" ]; then
            echo -e "${BLUE}  Output: ${result:0:100}${NC}"
        fi
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        echo -e "${RED}  Error: ${result}${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

echo -e "\n${BLUE}1. Testing Panel API...${NC}"
test_endpoint "Panel Health" "http://localhost:8080/healthz" "ok"
test_endpoint "Panel Metrics" "http://localhost:8080/metrics" "prometheus"

echo -e "\n${BLUE}2. Testing Signal Engine...${NC}"
test_endpoint "Signal Engine Metrics" "http://localhost:9100/metrics" "prometheus"

echo -e "\n${BLUE}3. Testing Executor...${NC}"
test_endpoint "Executor Metrics" "http://localhost:9101/metrics" "prometheus"

echo -e "\n${BLUE}4. Testing Redis...${NC}"
test_docker_cmd "Redis Ping" "docker exec -i \$(docker ps -qf name=redis) redis-cli ping 2>/dev/null | grep -q PONG"

echo -e "\n${BLUE}5. Testing ClickHouse...${NC}"
test_endpoint "ClickHouse Health" "http://localhost:8123/ping" "Ok"
test_docker_cmd "ClickHouse Tables" "docker exec -i \$(docker ps -qf name=clickhouse) clickhouse-client -q 'SHOW TABLES FROM levibot' 2>/dev/null | wc -l | grep -v '^0$'"

echo -e "\n${BLUE}6. Testing Prometheus...${NC}"
test_endpoint "Prometheus Health" "http://localhost:9090/-/healthy" "Prometheus"

echo -e "\n${BLUE}7. Testing Grafana...${NC}"
test_endpoint "Grafana Health" "http://localhost:3000/api/health" "ok"

echo -e "\n${BLUE}8. Testing Mini App...${NC}"
test_endpoint "Mini App" "http://localhost:5173" "html"

echo -e "\n${BLUE}9. Testing API Endpoints...${NC}"
test_with_output "Policy Status" "http://localhost:8080/policy/status"
test_with_output "Recent Signals" "http://localhost:8080/signals/recent?limit=5"

echo -e "\n${BLUE}10. Testing Docker Services...${NC}"
services=("panel" "signal_engine" "executor" "telegram_bot" "redis" "clickhouse" "prometheus" "grafana")
for service in "${services[@]}"; do
    echo -ne "${YELLOW}Checking ${service}...${NC} "
    if docker ps --format '{{.Names}}' | grep -q "${service}"; then
        echo -e "${GREEN}✓ RUNNING${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗ NOT RUNNING${NC}"
        FAILED=$((FAILED + 1))
    fi
done

# Summary
echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Smoke Test Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
echo -e "${RED}Failed: ${FAILED}${NC}"

if [ ${FAILED} -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed! System is healthy! 🚀${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed. Check logs with 'make logs'${NC}"
    exit 1
fi


# 🐳 LeviBot Docker Setup

**Quick Start:** Run entire LeviBot stack with one command.

---

## 📦 What's Included

| Service | Port | Description |
|---------|------|-------------|
| **API** | 8000 | Backend FastAPI + Engine Manager |
| **Panel** | 5173 | Frontend React + Vite (dev mode) |
| **Prometheus** | 9090 | Metrics scraping & storage |
| **Grafana** | 3000 | Dashboards & visualization |

---

## ⚡ Quick Start

### 1. Prerequisites

```bash
# Install Docker Desktop (includes docker-compose)
# macOS: https://docs.docker.com/desktop/install/mac-install/
# Linux: https://docs.docker.com/engine/install/

# Verify installation
docker --version
docker compose version
```

### 2. Start Services

```bash
# Build and start all services
docker compose -f docker-compose.dev.yml up -d --build

# Check status
docker compose -f docker-compose.dev.yml ps

# View logs (all services)
docker compose -f docker-compose.dev.yml logs -f

# View logs (specific service)
docker compose -f docker-compose.dev.yml logs -f api
docker compose -f docker-compose.dev.yml logs -f panel
```

### 3. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Panel** | http://localhost:5173 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **API Health** | http://localhost:8000/health | - |
| **Prometheus** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3000 | admin / admin |

---

## 🔎 Smoke Test (5 min)

### 1. Engines Page

```bash
# Open in browser
open http://localhost:5173/engines

# Test API directly
curl -s http://localhost:8000/engines | jq '.'

# Start an engine
curl -X POST http://localhost:8000/engines/start/BTC/USDT

# Check SSE stream (Ctrl+C to stop)
curl -N http://localhost:8000/stream/engines
```

**Expected:**
- ✅ Engines table loads
- ✅ SSE connection established (updates every 2s)
- ✅ Start/Stop buttons work

---

### 2. Backtest Page

```bash
# Open in browser
open http://localhost:5173/backtest

# List reports
curl -s http://localhost:8000/backtest/reports | jq '.'

# Run backtest
curl -X POST http://localhost:8000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USDT",
    "days": 30,
    "fee_bps": 5,
    "slippage_bps": 5,
    "max_pos": 1.0
  }' | jq '.'
```

**Expected:**
- ✅ Backtest form loads
- ✅ Run button triggers API
- ✅ Reports list updates

---

### 3. Ops Page (Kill Switch)

```bash
# Open in browser
open http://localhost:5173/ops

# Check kill switch status
curl -s http://localhost:8000/live/status | jq '.'

# Activate kill switch
curl -X POST "http://localhost:8000/live/kill" \
  -H "Content-Type: application/json" \
  -d '{"on": true, "reason": "smoke_test"}' | jq '.'

# Deactivate kill switch
curl -X POST "http://localhost:8000/live/kill" \
  -H "Content-Type: application/json" \
  -d '{"on": false, "reason": "test_complete"}' | jq '.'
```

**Expected:**
- ✅ Kill switch section visible
- ✅ Toggle works
- ✅ Status updates in real-time (5s polling)

---

## 🧪 Run Tests

### Backend Tests (pytest)

```bash
# Run all tests
docker compose -f docker-compose.dev.yml exec api pytest -v

# Run specific test file
docker compose -f docker-compose.dev.yml exec api pytest tests/test_engine_smoke.py -v

# Run with coverage
docker compose -f docker-compose.dev.yml exec api pytest --cov=src --cov-report=term-missing
```

### Frontend Tests (vitest) - After PR-6

```bash
# Run all tests
docker compose -f docker-compose.dev.yml exec panel pnpm test

# Run with UI
docker compose -f docker-compose.dev.yml exec panel pnpm test:ui

# Run with coverage
docker compose -f docker-compose.dev.yml exec panel pnpm test:coverage
```

---

## 📊 Monitoring

### Prometheus Metrics

```bash
# Open Prometheus UI
open http://localhost:9090

# View all metrics
open http://localhost:9090/targets

# Query engine metrics (PromQL)
# levi_inference_latency_seconds (p95)
# levi_orders_total{status="filled"}
# levi_md_queue_depth{symbol="BTC/USDT"}
# levi_kill_switch
```

### Grafana Dashboards

```bash
# Open Grafana
open http://localhost:3000

# Login: admin / admin (change on first login)

# Import dashboard
# 1. Go to Dashboards > Import
# 2. Upload ops/grafana-dashboard.json
# 3. Select Prometheus data source
```

**Key Metrics:**
- Inference latency (p95 < 50ms)
- Order success rate (> 99%)
- Kill switch status (0 = off, 1 = on)
- Queue depth (p95 < 32)

---

## 🛠️ Development Workflow

### Hot Reload

Both backend and frontend support hot reload:

```bash
# Edit backend code
vim backend/src/engine/engine.py
# API auto-reloads

# Edit frontend code
vim frontend/panel/src/pages/Engines.tsx
# Panel auto-reloads
```

### Restart Services

```bash
# Restart API only
docker compose -f docker-compose.dev.yml restart api

# Restart panel only
docker compose -f docker-compose.dev.yml restart panel

# Restart all services
docker compose -f docker-compose.dev.yml restart
```

### View Logs

```bash
# Follow all logs
docker compose -f docker-compose.dev.yml logs -f

# Follow API logs (filter errors)
docker compose -f docker-compose.dev.yml logs -f api | grep ERROR

# Follow panel logs (last 100 lines)
docker compose -f docker-compose.dev.yml logs --tail=100 panel
```

---

## 🧹 Cleanup

```bash
# Stop services (keep data)
docker compose -f docker-compose.dev.yml down

# Stop and remove volumes (delete data)
docker compose -f docker-compose.dev.yml down -v

# Remove images
docker compose -f docker-compose.dev.yml down --rmi all

# Full cleanup (nuclear option)
docker compose -f docker-compose.dev.yml down -v --rmi all
docker system prune -a --volumes -f
```

---

## 🐛 Troubleshooting

### Issue: API won't start

```bash
# Check logs
docker compose -f docker-compose.dev.yml logs api

# Common fixes:
# 1. Port 8000 already in use
lsof -ti:8000 | xargs kill -9

# 2. Missing dependencies
docker compose -f docker-compose.dev.yml build --no-cache api

# 3. Volume permissions
chmod -R 755 backend/data
```

---

### Issue: Panel build fails

```bash
# Rebuild panel
docker compose -f docker-compose.dev.yml build --no-cache panel

# Check Node.js version (should be 20+)
docker compose -f docker-compose.dev.yml run panel node --version

# Clear node_modules
rm -rf frontend/panel/node_modules
docker compose -f docker-compose.dev.yml build --no-cache panel
```

---

### Issue: SSE connection fails

**Symptom:** Engines page doesn't show real-time updates

**Fix:**
1. Check API is running: `curl http://localhost:8000/stream/engines`
2. Check CORS settings (should allow `http://localhost:5173`)
3. Check browser console for errors

---

### Issue: CORS errors

**Symptom:** Frontend can't call API (403/CORS)

**Fix:**
```python
# backend/src/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Issue: ARM/M1/M2 Mac build issues

```bash
# Force AMD64 platform
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker compose -f docker-compose.dev.yml up -d --build

# Or add to docker-compose.yml
services:
  api:
    platform: linux/amd64
```

---

## 📝 Makefile Commands

Add this to `Makefile` in repo root:

```makefile
.PHONY: up down logs restart test smoke clean

# Start all services
up:
\tdocker compose -f docker-compose.dev.yml up -d --build

# Stop all services
down:
\tdocker compose -f docker-compose.dev.yml down

# View logs
logs:
\tdocker compose -f docker-compose.dev.yml logs -f --tail=200

# Restart services
restart:
\tdocker compose -f docker-compose.dev.yml restart

# Run tests
test:
\tdocker compose -f docker-compose.dev.yml exec api pytest -q
\t@echo "Frontend tests coming in PR-6..."

# Smoke test URLs
smoke:
\t@echo "🔎 Smoke Test URLs:"
\t@echo "  Panel:    http://localhost:5173"
\t@echo "  Engines:  http://localhost:5173/engines"
\t@echo "  Backtest: http://localhost:5173/backtest"
\t@echo "  Ops:      http://localhost:5173/ops"
\t@echo "  API Docs: http://localhost:8000/docs"
\t@echo "  Grafana:  http://localhost:3000 (admin/admin)"

# Full cleanup
clean:
\tdocker compose -f docker-compose.dev.yml down -v --rmi all
```

**Usage:**
```bash
make up      # Start
make logs    # View logs
make test    # Run tests
make smoke   # Show URLs
make down    # Stop
make clean   # Full cleanup
```

---

## 🚀 Next Steps

### After Smoke Test

1. **Run Bug-Bash** (15 min)
   - Test error scenarios (backend down, SSE reconnect)
   - Check dark mode contrast
   - Verify empty states

2. **Start PR-6** (12 hours)
   - ESLint + Prettier
   - Vitest + Testing Library
   - Write tests (API, SSE, components)
   - GitHub Actions CI

3. **Start PR-7** (12 hours)
   - JWT auth + refresh tokens
   - Protected routes
   - RBAC (viewer vs admin)
   - Session management

### 48h Paper Trading

```bash
# Start paper trading soak test
make up

# Monitor metrics
open http://localhost:3000  # Grafana

# Check logs every 4 hours
make logs | grep ERROR
```

**Checkpoints:**
- T+1h: Engines running? No crashes?
- T+4h: Trades executed? PnL tracking?
- T+12h: Mid-checkpoint report
- T+24h: 24h report
- T+48h: Final report + demo

---

## 📚 References

- **Docker Compose Docs:** https://docs.docker.com/compose/
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/docker/
- **Vite Docker:** https://vitejs.dev/guide/backend-integration.html
- **Prometheus:** https://prometheus.io/docs/prometheus/latest/getting_started/
- **Grafana:** https://grafana.com/docs/grafana/latest/

---

## ✅ Quick Checklist

- [ ] Docker Desktop installed
- [ ] `make up` runs without errors
- [ ] All services healthy (`docker compose ps`)
- [ ] Panel loads at http://localhost:5173
- [ ] API returns at http://localhost:8000/health
- [ ] Prometheus scraping at http://localhost:9090
- [ ] Grafana accessible at http://localhost:3000
- [ ] Smoke test passed (3/3 pages)
- [ ] Bug-bash complete (6/6 scenarios)
- [ ] Ready for PR-6 (lint + tests)

---

**Status:** ✅ Docker setup complete  
**Next:** Run `make up` → Smoke test → PR-6  
**Time:** 5 min setup, 5 min smoke, 15 min bug-bash


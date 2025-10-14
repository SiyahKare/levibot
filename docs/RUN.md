# 🚀 LEVIBOT Quick Start Guide

## Prerequisites

- Docker & Docker Compose
- Python 3.11+
- PostgreSQL client (for manual DB init)

## Quick Start (Automated)

### 1. Start All Services

```bash
make up
```

This starts:

- TimescaleDB (5432)
- Redis (6379)
- FastAPI Backend (8000)
- React Panel (3001)

### 2. Initialize Database (First Time Only)

```bash
# Connect and run migrations
psql -h localhost -U postgres -d levibot -f backend/sql/001_timescale_init.sql
psql -h localhost -U postgres -d levibot -f backend/sql/010_caggs.sql
```

**Or using Docker:**

```bash
docker exec -i levibot-timescaledb psql -U postgres -d levibot < backend/sql/001_timescale_init.sql
docker exec -i levibot-timescaledb psql -U postgres -d levibot < backend/sql/010_caggs.sql
```

### 3. Verify Health

```bash
make check
```

Expected output:

```
✅ ALL SYSTEMS OPERATIONAL
```

### 4. View Logs

```bash
make logs
```

## Manual Start (Development)

### Terminal 1: Backend API

```bash
cd /Users/onur/levibot
source .venv/bin/activate
export PYTHONPATH=/Users/onur/levibot
export REDIS_URL=redis://localhost:6379/0
export PG_DSN=postgresql://postgres:postgres@localhost:5432/levibot
export SECURITY_ENABLED=false
uvicorn backend.src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Terminal 2: MEXC WebSocket Feed

```bash
source .venv/bin/activate
export PYTHONPATH=/Users/onur/levibot
export REDIS_URL=redis://localhost:6379/0
export PG_DSN=postgresql://postgres:postgres@localhost:5432/levibot
export SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
python -m backend.src.market.ws_mexc
```

### Terminal 3: Realtime Dispatcher

```bash
source .venv/bin/activate
export PYTHONPATH=/Users/onur/levibot
export REDIS_URL=redis://localhost:6379/0
export PG_DSN=postgresql://postgres:postgres@localhost:5432/levibot
python -m backend.src.realtime.dispatcher
```

### Terminal 4: Frontend Panel

```bash
cd frontend/panel
npm install
npm run dev
```

## URLs

- **Panel**: http://localhost:3001
- **API Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **Health**: http://localhost:8000/healthz

## Common Commands

```bash
# Start services
make up

# Stop services
make down

# Health check
make check

# View logs
make logs

# Restart services
make restart

# Clean (remove volumes)
make clean

# Run tests
pytest backend/tests/test_realtime_health.py -v
```

## Validation Script

Run comprehensive health check:

```bash
python3 scripts/validate_realtime.py
```

This checks:

- ✅ Port availability
- ✅ API health & metrics
- ✅ SSE stream connectivity
- ✅ Redis streams
- ✅ TimescaleDB hypertables
- ✅ Paper trading engine
- ✅ Panel availability

## Troubleshooting

### Services not starting

```bash
docker-compose ps
docker-compose logs api
```

### Database connection issues

```bash
# Check if TimescaleDB is healthy
docker exec levibot-timescaledb pg_isready

# Connect to database
psql -h localhost -U postgres -d levibot
```

### Redis issues

```bash
# Check Redis
redis-cli ping

# Check stream
redis-cli XLEN ticks
```

### Panel not loading

```bash
# Check nginx logs
docker-compose logs panel

# Rebuild panel
docker-compose build panel
docker-compose up -d panel
```

## Next Steps

1. **Configure Environment**: Copy `env.realtime.example` to `.env.docker`
2. **Add API Keys**: Set `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`
3. **Start WebSocket Feed**: Enable MEXC real-time data
4. **Monitor**: Check Prometheus metrics at `/metrics`
5. **Trade**: Use Paper Trading dashboard

## Support

For issues, check:

- `make logs` for service logs
- `/backend/data/logs/` for application events
- `make check` for health status

Happy trading! 🚀







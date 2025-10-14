# 🚀 LEVIBOT Realtime Runbook

## Quick Start (Docker)

```bash
# 1. Setup environment
cp .env.example .env.docker
# Edit .env.docker with your keys

# 2. Start all services
docker-compose up -d

# 3. Check health
docker-compose ps
curl http://localhost:8000/healthz
curl http://localhost:3001

# 4. View logs
docker-compose logs -f api
```

## Architecture

```
MEXC WebSocket → Redis XStream → Dispatcher → Paper Engine
                      ↓                           ↓
                TimescaleDB                   Metrics
                      ↓                           ↓
              Continuous Aggs              Prometheus
```

## Services

### 1. TimescaleDB (Port 5432)

- **Purpose**: Time-series market data storage
- **Init**: SQL migrations run automatically on first start
- **Access**: `psql -h localhost -U postgres -d levibot`
- **Health**: `docker exec levibot-timescaledb pg_isready`

**Manual Migration** (if needed):

```bash
docker exec -i levibot-timescaledb psql -U postgres -d levibot < backend/sql/001_timescale_init.sql
docker exec -i levibot-timescaledb psql -U postgres -d levibot < backend/sql/010_caggs.sql
```

### 2. Redis (Port 6379)

- **Purpose**: Real-time data streams & rate limiting
- **Streams**: `ticks`, `signals`, `events`
- **Health**: `redis-cli -h localhost ping`
- **Monitor**: `redis-cli -h localhost MONITOR`

**Stream Inspection**:

```bash
# Check stream length
redis-cli XLEN ticks

# Read latest 10 ticks
redis-cli XREVRANGE ticks + - COUNT 10

# Get last tick price
redis-cli HGETALL last:BTCUSDT
```

### 3. API (Port 8000)

- **Purpose**: FastAPI backend with SSE streams
- **Docs**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics (Prometheus format)
- **Health**: http://localhost:8000/healthz

**Key Endpoints**:

- `GET /stream/ticks` - SSE stream of market ticks
- `GET /stream/portfolio` - SSE stream of portfolio updates
- `GET /paper/portfolio` - Current portfolio stats
- `POST /trade/auto` - Execute auto-trade

### 4. Panel (Port 3001)

- **Purpose**: React dashboard with real-time updates
- **URL**: http://localhost:3001
- **Features**: Live prices, portfolio, AI insights

## Development Workflow

### Local (without Docker)

#### Terminal 1: API

```bash
cd /Users/onur/levibot
source .venv/bin/activate
export PYTHONPATH=/Users/onur/levibot
export REDIS_URL=redis://localhost:6379/0
export PG_DSN=postgresql://postgres:postgres@localhost:5432/levibot
export SECURITY_ENABLED=false
uvicorn backend.src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: MEXC WebSocket Feed

```bash
source .venv/bin/activate
export PYTHONPATH=/Users/onur/levibot
export REDIS_URL=redis://localhost:6379/0
export PG_DSN=postgresql://postgres:postgres@localhost:5432/levibot
export SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
python -m backend.src.market.ws_mexc
```

#### Terminal 3: Realtime Dispatcher

```bash
source .venv/bin/activate
export PYTHONPATH=/Users/onur/levibot
export REDIS_URL=redis://localhost:6379/0
export PG_DSN=postgresql://postgres:postgres@localhost:5432/levibot
python -m backend.src.realtime.dispatcher
```

#### Terminal 4: Frontend

```bash
cd frontend/panel
npm install
npm run dev
```

## Configuration

### Environment Variables

| Variable                | Default           | Description                          |
| ----------------------- | ----------------- | ------------------------------------ |
| `PAPER`                 | `true`            | Paper trading mode                   |
| `EXCHANGE`              | `MEXC`            | Exchange name                        |
| `SYMBOLS`               | `BTCUSDT,ETHUSDT` | Trading symbols (comma-separated)    |
| `REDIS_URL`             | -                 | Redis connection string              |
| `PG_DSN`                | -                 | PostgreSQL/TimescaleDB DSN           |
| `OPENAI_API_KEY`        | -                 | OpenAI API key for signal extraction |
| `TELEGRAM_BOT_TOKEN`    | -                 | Telegram bot token                   |
| `SLIPPAGE_BPS`          | `2.0`             | Slippage in basis points             |
| `FEE_TAKER_BPS`         | `5.0`             | Taker fee in basis points            |
| `MAX_DAILY_LOSS`        | `-200.0`          | Max daily loss (negative)            |
| `MAX_POS_NOTIONAL`      | `2000.0`          | Max position size in USD             |
| `WS_RECONNECT_SECS`     | `3`               | WebSocket reconnect interval         |
| `DB_BATCH_SIZE`         | `500`             | TimescaleDB batch size               |
| `DB_FLUSH_INTERVAL_SEC` | `0.25`            | TimescaleDB flush interval           |

## Monitoring

### Prometheus Metrics

Key metrics exposed at `/metrics`:

- `levibot_equity` - Current portfolio equity
- `levibot_unrealized_pnl` - Unrealized PnL
- `levibot_realized_pnl_total` - Total realized PnL
- `levibot_open_positions` - Number of open positions
- `levibot_http_requests_total` - HTTP request counter
- `levibot_http_request_latency_seconds` - Request latency histogram

### TimescaleDB Queries

```sql
-- Latest tick prices
SELECT symbol, last, ts
FROM market_ticks
WHERE ts > NOW() - INTERVAL '1 minute'
ORDER BY ts DESC
LIMIT 10;

-- 1-minute candles
SELECT bucket, symbol, open, high, low, close, volume
FROM candle_1m
WHERE symbol = 'BTCUSDT' AND bucket > NOW() - INTERVAL '1 hour'
ORDER BY bucket DESC;

-- Equity curve
SELECT ts, equity, unrealized, drawdown
FROM equity_curve
ORDER BY ts DESC
LIMIT 100;

-- Trading activity
SELECT DATE_TRUNC('hour', ts) as hour, COUNT(*), AVG(pnl)
FROM trades
WHERE is_paper = TRUE
GROUP BY hour
ORDER BY hour DESC;
```

## Troubleshooting

### WebSocket Feed Not Receiving Data

```bash
# Check if Redis streams are active
redis-cli XLEN ticks

# If 0, restart MEXC feed
docker-compose restart ws_feed  # (if containerized)
# OR
pkill -f ws_mexc && python -m backend.src.market.ws_mexc
```

### Dispatcher Not Processing

```bash
# Check Redis stream consumer lag
redis-cli XINFO GROUPS ticks

# Check dispatcher logs
docker-compose logs dispatcher

# Restart dispatcher
docker-compose restart dispatcher
```

### Database Connection Issues

```bash
# Check PostgreSQL health
docker exec levibot-timescaledb pg_isready

# Test connection
psql postgresql://postgres:postgres@localhost:5432/levibot -c "SELECT version();"

# Check connection pool
docker-compose logs api | grep "pool"
```

### High Memory Usage

```bash
# Redis memory stats
redis-cli INFO memory

# Reduce stream retention
redis-cli CONFIG SET stream-node-max-bytes 4096

# TimescaleDB compression check
psql -U postgres -d levibot -c "SELECT * FROM timescaledb_information.chunks WHERE is_compressed = false;"
```

## Performance Tuning

### Redis Streams

```bash
# Adjust max length (in .env)
STREAM_MAXLEN=10000  # Reduce if memory constrained
```

### TimescaleDB

```sql
-- Enable compression on old chunks (automatic via policy, but can force)
SELECT compress_chunk(c) FROM show_chunks('market_ticks') c LIMIT 10;

-- Check compression ratio
SELECT pg_size_pretty(before_compression_total_bytes) as before,
       pg_size_pretty(after_compression_total_bytes) as after,
       ROUND(after_compression_total_bytes::numeric / before_compression_total_bytes::numeric * 100, 2) as ratio_pct
FROM chunk_compression_stats('market_ticks');
```

### API

```yaml
# In docker-compose.yml, adjust worker count
command: uvicorn backend.src.app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Testing

### Smoke Test

```bash
# API health
curl http://localhost:8000/healthz

# Stream connectivity (should not timeout)
curl -N http://localhost:8000/stream/ticks &
sleep 5
killall curl

# Execute test trade
curl -X POST http://localhost:8000/trade/auto \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTCUSDT","side":"buy","notional_usd":50}'

# Check portfolio
curl http://localhost:8000/paper/portfolio | jq
```

### Load Test

```bash
# Install hey (HTTP load generator)
# brew install hey (macOS)

# Test /paper/portfolio endpoint
hey -n 1000 -c 50 http://localhost:8000/paper/portfolio
```

## Backup & Recovery

### TimescaleDB Backup

```bash
# Full backup
docker exec levibot-timescaledb pg_dump -U postgres levibot > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i levibot-timescaledb psql -U postgres levibot < backup_20250109.sql
```

### Redis Persistence

Redis AOF is enabled by default. Data persists in `redis_data` volume.

```bash
# Manual snapshot
redis-cli BGSAVE

# Check last save
redis-cli LASTSAVE
```

## Deployment Checklist

- [ ] Set all API keys in `.env.docker`
- [ ] Configure `SYMBOLS` for markets to trade
- [ ] Adjust risk limits (`MAX_DAILY_LOSS`, `MAX_POS_NOTIONAL`)
- [ ] Enable security: `SECURITY_ENABLED=true`
- [ ] Set up Prometheus scraping
- [ ] Configure alert channels (Telegram, Slack)
- [ ] Test WebSocket reconnection
- [ ] Verify TimescaleDB retention policies
- [ ] Set up automated backups
- [ ] Monitor initial equity curve

## Support

For issues, check:

1. `docker-compose logs <service>`
2. `/backend/data/logs/` for application events
3. TimescaleDB logs: `docker logs levibot-timescaledb`
4. Redis logs: `docker logs levibot-redis`

Happy trading! 🚀







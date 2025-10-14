# 🚀 MEXC Exchange Integration

MEXC spot trading integration via CCXT with full risk management, rate limiting, and metrics.

## 📋 Overview

LeviBot now supports live trading on MEXC exchange with:

- ✅ **Spot Market Orders** - Buy/sell at market price
- ✅ **Risk Management** - Cooldowns, notional limits, TP/SL derivation
- ✅ **Rate Limiting** - CCXT throttle + Redis distributed limits
- ✅ **Metrics** - Prometheus metrics for all order activity
- ✅ **Health Monitoring** - Balance, markets, ticker endpoints
- ✅ **Dry-Run Testing** - Safe testing without real orders

## 🔧 Configuration

### Environment Variables

Add to your `.env` file:

```bash
# Exchange Selection
EXCHANGE=MEXC                  # PAPER | MEXC (default: PAPER)

# MEXC API Credentials
MEXC_ENABLE=true              # Enable/disable MEXC executor
MEXC_API_KEY=your_api_key     # MEXC API key
MEXC_API_SECRET=your_secret   # MEXC API secret

# Optional Settings
MEXC_SANDBOX=false            # Use sandbox/testnet (limited support)
MEXC_RECV_WINDOW_MS=5000      # API request tolerance window
MEXC_RATE_LIMIT_MS=50         # CCXT throttle (ms between requests)
```

### API Key Setup

1. **Create API Keys** on [MEXC](https://www.mexc.com/):

   - Go to Account → API Management
   - Create new API key with "Spot Trading" permission
   - **Important:** Enable IP whitelist for security

2. **Permissions Required:**

   - ✅ Read (required for balance, markets)
   - ✅ Spot Trading (required for orders)
   - ❌ Withdraw (not needed, disable for security)

3. **Security Best Practices:**
   - Use IP whitelist (add your server IP)
   - Store keys in secure vault (not in git)
   - Use read-only keys for testing
   - Start with small notional amounts

## 🧪 Testing

### 1. Health Check (Safe)

```bash
# Check exchange connectivity
curl http://localhost:8000/exchange/ping | jq

# Expected response:
# {
#   "ok": true,
#   "exchange": "mexc",
#   "markets_count": 1500+
# }
```

### 2. Market Data (Safe)

```bash
# List available markets
curl http://localhost:8000/exchange/markets?limit=10 | jq

# Get ticker price
curl http://localhost:8000/exchange/ticker/BTCUSDT | jq

# Expected:
# {
#   "ok": true,
#   "exchange": "mexc",
#   "symbol": "BTC/USDT",
#   "price": 43250.50
# }
```

### 3. Account Balance (Safe)

```bash
# Fetch account balance
curl http://localhost:8000/exchange/balance | jq
```

### 4. Dry-Run Order Test (Safe)

```bash
# Test order without execution
curl "http://localhost:8000/exchange/test-order?symbol=BTCUSDT&side=buy&notional_usd=10&dry_run=true" | jq

# Expected:
# {
#   "ok": true,
#   "mode": "dry_run",
#   "symbol": "BTCUSDT",
#   "side": "buy",
#   "qty": 0.000232,
#   "price": 43250.50,
#   "filled": true
# }
```

### 5. Live Order Test (⚠️ CAUTION!)

```bash
# Small live order (use small notional!)
curl "http://localhost:8000/exchange/test-order?symbol=BTCUSDT&side=buy&notional_usd=5&dry_run=false" | jq
```

### Automated Smoke Test

Run the complete test suite:

```bash
# Dry-run tests (safe)
./backend/scripts/test_mexc.sh

# Live order tests (use with caution!)
./backend/scripts/test_mexc.sh live
```

## 📊 Monitoring

### Metrics (Prometheus)

```bash
# Check execution metrics
curl http://localhost:8000/metrics/prom | grep levibot_exec_orders_total
```

Metrics include:

- `levibot_exec_orders_total{exchange="mexc",status="ok|error|blocked",type="market"}`

### Event Logs

All orders are logged to JSONL:

```bash
# View recent order events
tail -f backend/data/logs/$(date +%Y-%m-%d)/events.jsonl | jq 'select(.event_type | contains("ORDER"))'
```

Event types:

- `ORDER_NEW` - Order submitted
- `ORDER_FILLED` - Order executed
- `ORDER_BLOCKED` - Risk check rejected
- `ORDER_ERROR` - Execution failed
- `RISK_SLTP` - TP/SL calculated

## 🔄 Auto-Trading Integration

To enable auto-trading with MEXC:

```bash
# Enable auto-route with MEXC
AUTO_ROUTE_ENABLED=true
AUTO_ROUTE_DRY_RUN=false          # ⚠️ Set to false for live trading
AUTO_ROUTE_EXCH=mexc              # Use MEXC executor
AUTO_ROUTE_MIN_CONF=0.75
AUTO_ROUTE_DEFAULT_NOTIONAL=25
```

Signal flow:

1. Telegram signal ingested
2. ML model scores signal
3. If confidence ≥ threshold → auto-route
4. Risk checks applied
5. Order placed on MEXC
6. TP/SL calculated and logged

## 🛡️ Risk Management

### Built-in Protections

1. **Notional Clamps:**

   ```bash
   RISK_MIN_NOTIONAL=5    # Minimum order size
   RISK_MAX_NOTIONAL=250  # Maximum order size
   ```

2. **Cooldown Period:**

   - Per-symbol cooldown after order
   - Prevents rapid repeated orders

3. **Position Limits:**

   - Max positions per symbol
   - Max total exposure

4. **TP/SL Derivation:**
   - Automatic stop-loss calculation
   - Take-profit based on risk/reward
   - Policy-based multipliers (conservative/moderate/aggressive)

### Risk Policies

```bash
RISK_POLICY=moderate  # conservative | moderate | aggressive
```

| Policy       | SL ATR Multiple | TP R:R | Max Notional |
| ------------ | --------------- | ------ | ------------ |
| conservative | 1.5x            | 2:1    | $100         |
| moderate     | 2.0x            | 2.5:1  | $250         |
| aggressive   | 2.5x            | 3:1    | $500         |

## 🚨 Error Handling

### Common Errors

**"Unknown symbol for MEXC"**

- Symbol format incorrect (use `BTCUSDT` or `BTC/USDT`)
- Market not available on MEXC

**"Order blocked by risk check"**

- Cooldown period active
- Notional exceeds limits
- Check `ORDER_BLOCKED` events in logs

**"429 Too Many Requests"**

- Rate limit exceeded
- Increase `MEXC_RATE_LIMIT_MS` (e.g., 100)

**"Invalid API key"**

- Check `MEXC_API_KEY` and `MEXC_API_SECRET`
- Verify IP whitelist on MEXC

### Debug Mode

```bash
# Enable detailed logging
export LOG_LEVEL=DEBUG

# Watch all MEXC events
tail -f backend/data/logs/$(date +%Y-%m-%d)/events.jsonl | jq 'select(.event_type | contains("MEXC"))'
```

## 📈 Production Deployment

### Pre-flight Checklist

- [ ] API keys configured with IP whitelist
- [ ] Tested with dry-run mode
- [ ] Tested with small live orders ($5-10)
- [ ] Risk limits configured appropriately
- [ ] Monitoring/alerts setup (Prometheus/Grafana)
- [ ] Backup plan for API downtime

### Deployment Steps

1. **Stage Environment:**

   ```bash
   cp .env.example .env.prod
   # Edit .env.prod with MEXC credentials
   ```

2. **Test in Docker:**

   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ./backend/scripts/test_mexc.sh
   ```

3. **Monitor First Orders:**

   ```bash
   # Watch metrics
   watch -n 5 'curl -s http://localhost:8000/metrics/prom | grep levibot_exec_orders_total'

   # Watch logs
   tail -f backend/data/logs/$(date +%Y-%m-%d)/events.jsonl
   ```

4. **Enable Auto-Trading:**

   ```bash
   # Gradually increase confidence threshold
   AUTO_ROUTE_MIN_CONF=0.85  # Start conservative

   # Monitor for 24h, then lower to 0.75-0.80
   ```

### Rollback Plan

If issues occur:

```bash
# Immediate: Switch back to paper mode
export EXCHANGE=PAPER

# Or: Disable auto-route
export AUTO_ROUTE_ENABLED=false

# Restart API
docker-compose restart api
```

## 🔐 Security

### Key Management

**Development:**

```bash
# Use .env (gitignored)
echo "MEXC_API_KEY=xxx" >> .env
```

**Production:**

```bash
# Use Docker secrets or vault
docker secret create mexc_api_key /path/to/key
docker secret create mexc_api_secret /path/to/secret
```

### IP Whitelist

Always enable IP whitelist on MEXC:

1. Get your server IP: `curl ifconfig.me`
2. Add to MEXC API key settings
3. Test connectivity after adding

### Audit Trail

All orders logged with:

- Timestamp
- Symbol, side, quantity
- Price, notional
- Trace ID (for debugging)
- Risk checks applied

## 📚 API Reference

### Endpoints

| Endpoint                    | Method | Description                     |
| --------------------------- | ------ | ------------------------------- |
| `/exchange/ping`            | GET    | Health check                    |
| `/exchange/balance`         | GET    | Account balance                 |
| `/exchange/markets`         | GET    | Available markets               |
| `/exchange/ticker/{symbol}` | GET    | Current price                   |
| `/exchange/test-order`      | POST   | Place order (dry-run supported) |

### Response Format

All endpoints return:

```json
{
  "ok": true|false,
  "error": "error message (if ok=false)",
  // ... endpoint-specific fields
}
```

## 🤝 Support

**Issues:**

- Check logs: `backend/data/logs/`
- Run smoke test: `./backend/scripts/test_mexc.sh`
- Check metrics: `/metrics/prom`

**Resources:**

- [MEXC API Docs](https://mexcdevelop.github.io/apidocs/)
- [CCXT Documentation](https://docs.ccxt.com/)
- [LeviBot Architecture](./ARCHITECTURE.md)

---

**Version:** 1.7.0  
**Last Updated:** October 7, 2025  
**Status:** ✅ Production Ready

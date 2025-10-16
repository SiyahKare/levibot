# 48H Soak Test - LeviBot v1.8.0-beta

## Test Details
- **Start Time**: 2025-10-16 08:36:14 +03
- **Duration**: 48 hours
- **End Time**: 2025-10-18 08:36:14 +03
- **Symbols**: BTC/USDT, ETH/USDT, SOL/USDT
- **Mode**: Paper Trading

## SLO Targets
- API Uptime: ≥ 99.9%
- Engine Uptime: ≥ 99.5%
- Inference p95 (LGBM): ≤ 80ms
- Inference p95 (TFT): ≤ 40ms
- MD Drop Rate: ≤ 0.1%
- Errors/min: ≤ 1
- Global Stop: 0

## Checkpoint Schedule
- **T+1h**: 2025-10-16 09:36 → `checkpoint_T+1h.md`
- **T+6h**: 2025-10-16 14:36 → `checkpoint_T+6h.md`
- **T+24h**: 2025-10-17 08:36 → `checkpoint_T+24h.md`
- **T+48h**: 2025-10-18 08:36 → `checkpoint_T+48h.md` (FINAL)

## Monitoring URLs
- Grafana SLO: http://localhost:3001/d/slo-overview
- Prometheus: http://localhost:9090
- Panel: http://localhost:3000
- API Health: http://localhost:8000/health

## Quick Commands
\`\`\`bash
# Engine status
curl -s http://localhost:8000/engines | jq

# Fibonacci levels
curl -s 'http://localhost:8000/ta/fibonacci?symbol=BTC/USDT&timeframe=1m&window=100' | jq

# Recent predictions
curl -s http://localhost:8000/analytics/predictions/recent | jq '.items[:5]'
\`\`\`

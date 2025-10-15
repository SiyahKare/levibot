###Backtest Framework v2 Guide

Production-grade vectorized backtest with fees, slippage, and latency-aware fills.

## Features

- ✅ Vectorized execution (fast)
- ✅ Transaction costs (fees + slippage)
- ✅ Latency-aware fills (order delay)
- ✅ Position sizing with risk caps
- ✅ Multiple benchmarks (Buy & Hold, SMA crossover)
- ✅ Comprehensive metrics (Sharpe, Sortino, MDD, CAGR, Hit Rate, Turnover)
- ✅ Multi-format reports (MD, JSON, HTML)
- ✅ CI/CD integration (nightly gates)

---

## Quick Start

```bash
# 1. Run single backtest
python -m backend.src.backtest.cli run \
  --bars backend/data/bars/BTCUSDT_1m.parquet \
  --signal ensemble \
  --fee-bps 5 --slippage-bps 5 \
  --latency-ms 100 --risk-cap 0.2 \
  --out backend/reports/backtests/test_run

# 2. Batch backtests
python -m backend.src.backtest.cli batch \
  --symbols BTCUSDT,ETHUSDT,SOLUSDT \
  --days 90 \
  --out-dir backend/reports/backtests/batch

# 3. View HTML report
open backend/reports/backtests/test_run/report.html
```

---

## Performance Targets (DoD)

| Metric                  | Target             | Check                |
| ----------------------- | ------------------ | -------------------- |
| Sharpe (strategy)       | ≥ B&H + 0.2        | ✅ Report comparison |
| Sharpe regression       | ≥ 0.8 \* previous  | ✅ CI gate           |
| CAGR                    | > 0%               | ✅ Report            |
| Max Drawdown            | < 30%              | ✅ Report            |
| Hit Rate                | > 50%              | ✅ Report            |
| Report formats          | MD/JSON/HTML       | ✅ Generated         |
| CI nightly              | Runs + gates       | ✅ Workflow          |

---

## Architecture

```
backend/src/backtest/
├── runner_v2.py      # Core engine (fills, costs, latency)
├── strategies.py     # Signal -> position logic
├── metrics.py        # Performance metrics
├── report.py         # MD/JSON/HTML generation
├── cli.py            # Command-line interface
└── README_BACKTEST.md
```

---

## Metrics

### Sharpe Ratio
Annualized return / risk ratio. Target: **≥ B&H + 0.2**

### Sortino Ratio
Like Sharpe, but only penalizes downside volatility.

### Maximum Drawdown (MDD)
Peak-to-trough decline. Target: **< 30%**

### CAGR
Compound Annual Growth Rate.

### Hit Rate
Percentage of profitable trades. Target: **> 50%**

### Turnover
Average position changes per period (annualized).

---

## Report Formats

### Markdown (`.md`)
Human-readable summary with tables.

### JSON (`.json`)
Machine-readable with full data (equity curve, positions, trades).

### HTML (`.html`)
Interactive report with charts (simplified - full version would use Chart.js/Plotly).

---

## CI/CD Integration

### Nightly Workflow
`.github/workflows/nightly-backtest.yml`

**Gates**:
1. `sharpe_strategy >= sharpe_bh + 0.2` (fail if not)
2. `sharpe_strategy >= 0.8 * sharpe_previous` (fail if regressed)
3. Reports exist and JSON is valid (fail if missing)

**Artifacts**: Reports uploaded for 30 days.

---

## Troubleshooting

### Low Sharpe Ratio
- Check signal quality (ML model performance)
- Increase risk cap (if too conservative)
- Reduce fees/slippage (if unrealistic)

### High Drawdown
- Reduce risk cap
- Add stop-loss logic
- Review signal accuracy during drawdown periods

### Slow Execution
- Backtest is vectorized, should be fast
- Check bar count (90d 1m = ~130K bars)
- Profile with `cProfile` if needed

---

## Next Steps

1. **Gün 6**: Kill switch + chaos testing
2. **Gün 7**: 24h soak test + GO/NO-GO

---

**Status**: ✅ Production-ready, vectorized, gate-protected!


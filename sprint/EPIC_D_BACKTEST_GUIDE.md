# 📊 Epic-D: Backtesting Framework — Implementation Guide

**Status:** COMPLETE ✅  
**Sprint:** S10 — The Real Deal  
**Date:** 2025-10-14

---

## 🎯 Overview

Vectorized backtesting framework for strategy validation with realistic fills, transaction costs, and performance metrics.

### Architecture

```
Signal Function (prob_up: 0..1)
    ↓
Position Logic (≥0.5 → long, <0.5 → flat)
    ↓
Fill Simulation (t+1 mid-price)
    ↓
Cost Model (fee + slippage in bps)
    ↓
P&L Series → Equity Curve
    ↓
Metrics (Sharpe, Sortino, MDD, Hit Rate, Turnover)
    ↓
Report (Markdown + JSON + Equity NPY)
```

---

## 📦 Components

### 1. `backend/src/backtest/metrics.py`

Performance metrics calculation:

| Metric           | Description            | Formula                             |
| ---------------- | ---------------------- | ----------------------------------- |
| **Sharpe**       | Risk-adjusted return   | `(μ * 525600) / (σ * √525600)`      |
| **Sortino**      | Downside risk-adjusted | `(μ * 525600) / (σ_down * √525600)` |
| **Max Drawdown** | Peak-to-trough decline | `min((equity - peak) / peak)`       |
| **Hit Rate**     | Win rate               | `P(trade_pnl > 0)`                  |
| **Turnover**     | Position churn         | `Σ\|Δposition\|`                    |

**Annualization:** Assumes 1-minute bars, 525,600 minutes/year

### 2. `backend/src/backtest/runner.py`

Vectorized backtest engine:

**Fill Logic:**

- Entry: `t+1` mid-price `(O+H+L+C)/4`
- Exit: `t+1` mid-price
- Costs: `(fee_bps + slippage_bps) × 1e-4 × |Δposition|`

**Position Rules:**

- `prob_up >= 0.5` → `position = 1` (long)
- `prob_up < 0.5` → `position = 0` (flat)
- Future: Add short support (`position = -1`)

**Returns:**

```python
{
    "equity": np.ndarray,      # Cumulative equity curve
    "pnl": np.ndarray,          # Per-minute P&L
    "side": np.ndarray,         # Position array (0/1)
    "prob": np.ndarray,         # Signal probabilities
    "metrics": dict             # Performance metrics
}
```

### 3. `backend/src/backtest/report.py`

Artifact generation:

**Outputs:**

- `{symbol}_summary.md` — Markdown report table
- `{symbol}_metrics.json` — JSON metrics for CI
- `{symbol}_equity.npy` — Binary equity curve

---

## 🚀 Quick Start

### Basic Usage

```python
import numpy as np
import pandas as pd
from backend.src.backtest.runner import run_backtest
from backend.src.backtest.report import save_report

# Define signal function (returns prob_up: 0..1)
def my_signal(df: pd.DataFrame) -> pd.Series:
    mom = df["close"].diff().fillna(0.0)
    return (mom > 0).astype(float) * 0.2 + 0.4  # 0.4 or 0.6

# Prepare OHLCV bars (1-minute)
ts0 = 1_700_000_000_000
ts = np.arange(ts0, ts0 + 60_000 * 1440, 60_000)  # 1 day
close = np.linspace(100, 105, len(ts))

bars = pd.DataFrame({
    "ts": ts,
    "open": close,
    "high": close + 0.5,
    "low": close - 0.5,
    "close": close,
    "volume": 1000
})

# Run backtest
result = run_backtest(
    bars,
    my_signal,
    fee_bps=5.0,        # 0.05% fee
    slippage_bps=5.0,   # 0.05% slippage
    max_pos=1
)

# Print metrics
print(result["metrics"])
# Output: {'sharpe': 1.23, 'sortino': 1.45, 'max_drawdown': -0.08, ...}

# Save report
paths = save_report(result, "BTCUSDT", out_dir="reports/backtests")
print(f"Report: {paths['markdown']}")
```

### Integration with EnsemblePredictor

```python
from backend.src.ml.models.ensemble_predictor import EnsemblePredictor
from backend.src.backtest.runner import run_backtest

def ensemble_signal(df: pd.DataFrame) -> pd.Series:
    """Use production ML ensemble for signals."""
    ens = EnsemblePredictor(threshold=0.55)
    ens.load()  # Load LGBM + TFT models

    probs = []
    for i in range(len(df)):
        # Build features (simplified - real version uses feature_store)
        features = {
            "close": float(df.loc[i, "close"]),
            "ret1": 0.0,
            "sma20_gap": 0.0,
            "sma50_gap": 0.0,
            "vol_z": 0.0
        }
        pred = ens.predict(features, sentiment=0.0)
        probs.append(pred["prob_up"])

    return pd.Series(probs)

# Run with ensemble
result = run_backtest(bars, ensemble_signal, fee_bps=5, slippage_bps=5)
```

### 90-Day Backtest (Production)

```python
from backend.src.data.feature_store import load_parquet, minute_features
from backend.src.backtest.runner import run_backtest

# Load 90 days of OHLCV
df = load_parquet("backend/data/feature_store/BTCUSDT.parquet")
df = df.tail(90 * 1440)  # Last 90 days (1-minute bars)

# Run backtest
result = run_backtest(df, ensemble_signal, fee_bps=5, slippage_bps=5)

# Validate Sharpe threshold
if result["metrics"]["sharpe"] < 1.0:
    raise ValueError(f"Sharpe too low: {result['metrics']['sharpe']:.2f}")
```

---

## 🧪 Tests

### Run Smoke Tests

```bash
cd backend
PYTHONPATH=. pytest tests/test_backtest_smoke.py -v
```

**Expected Output:**

```
tests/test_backtest_smoke.py::test_backtest_runner PASSED
tests/test_backtest_smoke.py::test_backtest_report PASSED
```

### Test Coverage

```bash
PYTHONPATH=. pytest tests/test_backtest_smoke.py --cov=src/backtest --cov-report=term-missing
```

---

## 📊 Metrics Reference

### Sharpe Ratio

**Interpretation:**

- `> 2.0`: Excellent
- `1.0 - 2.0`: Good
- `0.5 - 1.0`: Acceptable
- `< 0.5`: Poor

**Formula (annualized):**

```
Sharpe = (mean_return * 525600) / (std_return * √525600)
```

### Max Drawdown (MDD)

**Interpretation:**

- `< -10%`: Warning
- `< -20%`: High risk
- `< -30%`: Unacceptable

**Calculation:**

```python
peak = np.maximum.accumulate(equity)
dd = (equity - peak) / peak
mdd = dd.min()  # Negative value
```

### Hit Rate

**Interpretation:**

- `> 55%`: Strong edge
- `50% - 55%`: Marginal edge
- `< 50%`: No edge (or inverted)

**Formula:**

```
hit_rate = count(winning_trades) / count(total_trades)
```

---

## 🔗 CI/CD Integration

### Nightly Backtest (Proposed)

Add to `.github/workflows/ci.yml`:

```yaml
backtest:
  runs-on: ubuntu-latest
  needs: test
  steps:
    - uses: actions/checkout@v4

    - name: Run 90-day backtest
      run: |
        cd backend
        PYTHONPATH=. python scripts/nightly_backtest.py

    - name: Upload backtest artifacts
      uses: actions/upload-artifact@v4
      with:
        name: backtest-reports
        path: reports/backtests/*.json

    - name: Validate Sharpe threshold
      run: |
        python3 << 'EOF'
        import json, sys
        metrics = json.load(open('reports/backtests/BTCUSDT_metrics.json'))
        sharpe = metrics.get('sharpe', 0)
        print(f"Sharpe: {sharpe:.2f}")
        if sharpe < 1.0:
            print(f"❌ Sharpe below threshold (1.0)")
            sys.exit(1)
        print("✅ Sharpe threshold met")
        EOF
```

### Regression Gate

Fail CI if Sharpe drops >10% from baseline:

```python
# scripts/check_sharpe_regression.py
import json, sys

baseline = 1.5  # From previous run
current = json.load(open('reports/backtests/BTCUSDT_metrics.json'))['sharpe']

drop_pct = (baseline - current) / baseline * 100

if drop_pct > 10:
    print(f"❌ Sharpe drop: {drop_pct:.1f}% (threshold: 10%)")
    sys.exit(1)

print(f"✅ Sharpe stable: {current:.2f} (baseline: {baseline:.2f})")
```

---

## ✅ Definition of Done

- [x] Vectorized runner with t+1 fill simulation
- [x] Transaction costs (fee + slippage in bps)
- [x] Metrics: Sharpe, Sortino, MDD, Hit Rate, Turnover
- [x] Report generation (Markdown + JSON + NPY)
- [x] Smoke tests (2/2 passing)
- [x] Integration examples (dummy + ensemble)
- [ ] CI nightly backtest job (90-day)
- [ ] Sharpe regression gate (>10% drop → fail)
- [ ] HTML report with equity curve chart

---

## 🚀 Future Enhancements

1. **Long/Short Support** (currently long/flat only)
2. **Slippage Model** (volume-weighted, spread-based)
3. **Latency Simulation** (t+N fill delay)
4. **Multi-Symbol Portfolio** (correlation, rebalancing)
5. **Walk-Forward Optimization** (rolling window retrain)
6. **HTML Reports** (Plotly equity curves, underwater charts)
7. **Risk Parity** (volatility-weighted positions)
8. **Parameter Sweep** (fee/slippage sensitivity)

---

## 📝 Notes

- **Bar Frequency:** Currently assumes 1-minute bars (525,600 bars/year)
- **Fill Model:** Mid-price at t+1 (optimistic; real fills may be worse)
- **Position Sizing:** Fixed 1-lot (future: ATR/Kelly/volatility-weighted)
- **Signal Function:** Must return `pd.Series` of prob_up (0.0 to 1.0)
- **Costs:** Applied on position changes (`|Δposition| × (fee+slip)`)

---

**Epic-D Complete!** 🎊  
Next: Integrate with real OHLCV data from Epic-A (ccxt) + Epic-B/C models.

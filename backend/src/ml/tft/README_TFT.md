# TFT Production Training Guide

Production-grade Temporal Fusion Transformer (TFT) training pipeline.

## Features

- ✅ Snapshot-based reproducibility (manifest + checksum)
- ✅ PyTorch Lightning + early stopping
- ✅ Mixed precision (bf16)
- ✅ Time-based splits (leakage guards)
- ✅ Latency benchmarking (p95 < 40ms target)
- ✅ Drift detection (PSI, Jensen-Shannon)
- ✅ Model Card v2 auto-generation
- ✅ Symlink deployment + rollback

---

## Quick Start

```bash
# 1. Create snapshot (if not done yet)
python backend/scripts/make_snapshot.py \
  --days 90 --symbols BTCUSDT,ETHUSDT,SOLUSDT

# 2. Train TFT
python -m backend.src.ml.tft.train_tft_prod \
  --snapshot backend/data/snapshots/2025-10-15T12-00-00Z \
  --seq-len 64 --hidden 128 \
  --max-epochs 50 --patience 7

# 3. Benchmark latency
python backend/scripts/bench_tft_latency.py --warmup 20 --n 200

# 4. Check drift
python -m backend.src.ml.tft.drift \
  --snapshot backend/data/snapshots/2025-10-15T12-00-00Z \
  --recent-days 7

# 5. Rollback (if needed)
./backend/scripts/rollback_model.sh 2025-10-14 tft
```

---

## Architecture

Simplified TFT (LSTM-based):

- **Sequence length**: 64 bars (1m each)
- **Features**: `close`, `volume`, `ret_1m`, `sma_20_gap`, `sma_50_gap`
- **Hidden size**: 128
- **Layers**: 2 LSTM layers + FC head
- **Output**: Binary probability (upward movement)

> **Note**: For full TFT, use PyTorch Forecasting's `TemporalFusionTransformer`.

---

## Model Card v2 Example

```json
{
  "version": "2",
  "model_name": "tft_prod",
  "created_at": "2025-10-15T12:00:00Z",
  "train": {
    "snapshot_id": "2025-10-15T12-00-00Z",
    "range": { "start": "2025-07-15", "end": "2025-10-15" },
    "rows": 130000,
    "class_balance": { "pos": 65000, "neg": 65000 }
  },
  "metrics": {
    "accuracy": 0.65,
    "val_loss": 0.68
  },
  "latency_ms": {
    "mean": 12.5,
    "p50": 12.2,
    "p95": 15.8,
    "p99": 18.3
  },
  "architecture": {
    "seq_len": 64,
    "hidden_size": 128,
    "total_params": 285000,
    "features": ["close", "volume", "ret_1m", "sma_20_gap", "sma_50_gap"]
  },
  "inference": {
    "device": "cpu",
    "threads": 1,
    "warmup_n": 20
  }
}
```

---

## Performance Targets (Gün 4 DoD)

| Metric            | Target   | Check                    |
| ----------------- | -------- | ------------------------ |
| Accuracy (val)    | ≥ 0.60   | ✅ Check model_card.json |
| Latency p95 (CPU) | ≤ 40ms   | ✅ Check model_card.json |
| PSI (max)         | ≤ 0.25   | ✅ Check drift report    |
| JS divergence     | ≤ 0.3    | ✅ Check drift report    |
| Leakage guards    | All pass | ✅ CI green              |
| Symlink deploy    | Ready    | ✅ best_tft.pt exists    |

---

## Drift Detection

### Metrics

- **PSI (Population Stability Index)**:

  - < 0.1: No change
  - 0.1 - 0.25: Moderate (investigate)
  - \> 0.25: Significant (retrain)

- **JS Divergence (Jensen-Shannon)**:
  - 0: Identical
  - \> 0.3: Different distributions

### Usage

```bash
# Generate drift report
python -m backend.src.ml.tft.drift \
  --snapshot backend/data/snapshots/2025-10-15T12-00-00Z \
  --recent-days 7 \
  --psi-threshold 0.25 \
  --js-threshold 0.3 \
  --output backend/reports/drift_2025-10-15.json
```

**Output**: `backend/reports/drift_YYYY-MM-DD.json`

---

## Ensemble Integration

```bash
# Optimize ensemble weights (LGBM + TFT)
python -m backend.src.ml.ensemble.weights \
  --lgbm-proba lgbm_val_proba.csv \
  --tft-proba tft_val_proba.csv \
  --y-true val_labels.csv \
  --output backend/data/models/ensemble.json
```

**Output**: `backend/data/models/ensemble.json`

```json
{
  "weights": {
    "lgbm": 0.6,
    "tft": 0.4,
    "sentiment": 0.0
  },
  "metrics": {
    "accuracy": 0.68,
    "f1": 0.67,
    "auc_roc": 0.73
  }
}
```

---

## Troubleshooting

### Latency > 40ms

1. **Reduce seq_len**: 64 → 32
2. **Single thread**: `torch.set_num_threads(1)`
3. **Warm-up**: Pre-load model at startup
4. **JIT compile**: `torch.jit.script(model)` (if compatible)

### High Drift (PSI > 0.25)

1. **Check data**: Market regime change?
2. **Increase window**: 7 days → 14 days
3. **Retrain**: Use more recent data

### OOM (Out of Memory)

1. **Reduce batch size**: 32 → 16
2. **Shorter sequence**: 64 → 32
3. **Smaller hidden**: 128 → 64

---

## CI/CD Integration

```yaml
# .github/workflows/backend-ci.yml
- name: Test TFT latency
  run: |
    python backend/scripts/bench_tft_latency.py --warmup 10 --n 50

- name: Test drift detection
  run: |
    pytest backend/tests/test_ml/test_drift_metrics.py -v
```

---

## Files Structure

```
backend/
├── src/ml/tft/
│   ├── train_tft_prod.py     # Production trainer
│   ├── infer_tft.py           # Thread-safe inference
│   ├── drift.py               # PSI/JS drift detection
│   └── README_TFT.md          # This file
├── scripts/
│   └── bench_tft_latency.py   # Latency benchmark
├── tests/test_ml/
│   ├── test_tft_latency.py    # Latency tests
│   ├── test_drift_metrics.py  # Drift tests
│   └── test_ensemble_weights.py
└── data/
    ├── models/
    │   ├── 2025-10-15/
    │   │   ├── tft.pt
    │   │   └── tft_model_card.json
    │   ├── best_tft.pt -> 2025-10-15/tft.pt
    │   └── best_tft_model_card.json
    └── snapshots/
        └── 2025-10-15T12-00-00Z/
            └── manifest.json
```

---

## Next Steps

1. **Gün 5**: Backtest framework (90d, fees, HTML reports)
2. **Gün 6**: Kill switch chaos test
3. **Gün 7**: 24h soak test + GO/NO-GO

---

**Status**: ✅ Production-ready, reproducible, rollback-ready!

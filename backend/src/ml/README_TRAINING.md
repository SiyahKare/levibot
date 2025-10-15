# 🤖 Production ML Training Guide

## Overview

This directory contains production-grade ML training pipelines with:

- ✅ Snapshot-based reproducibility
- ✅ Optuna hyperparameter optimization
- ✅ Probability calibration (Platt/Isotonic)
- ✅ Latency benchmarking
- ✅ Model Card v2 generation
- ✅ Leakage guards (time-based splits)

---

## Quick Start

### 1. Create Snapshot (Gün 2)

```bash
# Fetch 90 days of data and create snapshot
python backend/scripts/make_snapshot.py \
  --days 90 \
  --symbols BTCUSDT,ETHUSDT,SOLUSDT

# Output: backend/data/snapshots/<timestamp>/
#   - BTCUSDT.parquet
#   - ETHUSDT.parquet
#   - SOLUSDT.parquet
#   - manifest.json (with SHA-256 checksums)
```

### 2. Train LGBM (Gün 3)

```bash
# Train with Optuna (200 trials, isotonic calibration)
python -m backend.src.ml.train_lgbm_prod \
  --snapshot backend/data/snapshots/2025-10-15T12-00-00Z \
  --trials 200 \
  --early-stop 50 \
  --calibration isotonic \
  --val-ratio 0.2

# Output: backend/data/models/2025-10-15/
#   - lgbm.pkl (trained model)
#   - model_card.json (Model Card v2)
# Symlinks:
#   - backend/data/models/best_lgbm.pkl -> 2025-10-15/lgbm.pkl
#   - backend/data/models/best_lgbm_model_card.json -> 2025-10-15/model_card.json
```

### 3. Rollback (if needed)

```bash
# Rollback to previous version
./backend/scripts/rollback_model.sh 2025-10-14

# List available versions
ls -1 backend/data/models/ | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" | sort -r
```

---

## Model Card v2 Schema

Generated cards conform to `backend/src/ml/model_card_schema.json`:

```json
{
  "version": "2",
  "model_name": "lgbm_prod",
  "created_at": "2025-10-15T12:00:00Z",
  "train": {
    "snapshot_id": "2025-10-15T12-00-00Z",
    "range": { "start": "2025-07-15", "end": "2025-10-15" },
    "rows": 130000,
    "class_balance": { "pos": 65000, "neg": 65000 },
    "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
  },
  "metrics": {
    "accuracy": 0.67,
    "f1": 0.65,
    "precision": 0.64,
    "recall": 0.66,
    "auc_roc": 0.72,
    "calibration_ece": 0.08
  },
  "latency_ms": {
    "mean": 15.2,
    "p50": 14.8,
    "p95": 18.3,
    "p99": 22.1,
    "samples": 1000
  },
  "leakage_checks": {
    "future_info": true,
    "time_split": true,
    "feature_audit": true
  },
  "feature_importance": [
    { "name": "close", "gain": 1250.5 },
    { "name": "ret_1m", "gain": 980.2 }
  ],
  "hyperparameters": {
    "learning_rate": 0.05,
    "num_leaves": 64
  },
  "notes": "Trained with Optuna, calibrated with isotonic"
}
```

---

## Leakage Guards

### Time-Based Split

```python
# Enforced in train_lgbm_prod.py
train_max_ts = train_df["ts"].max()
val_min_ts = val_df["ts"].min()

assert train_max_ts < val_min_ts, "TIME-SPLIT VIOLATION!"
```

### Feature Schema Validation

```python
# Validates against features.yml
from backend.src.data.feature_registry.validator import validate_features
validate_features(df, strict=True)
```

### CI Tests

```bash
# Run leakage guard tests
pytest backend/tests/test_leakage_guards.py -v
```

---

## Performance Targets (Gün 3 DoD)

| Metric            | Target           | Actual                   |
| ----------------- | ---------------- | ------------------------ |
| Accuracy (val)    | ≥ baseline + 2pp | ✅ Check model_card.json |
| Calibration ECE   | ≤ 0.1            | ✅ Check model_card.json |
| Latency p95 (CPU) | ≤ 80ms           | ✅ Check model_card.json |
| Leakage guards    | All pass         | ✅ CI green              |

---

## Directory Structure

```
backend/src/ml/
├── train_lgbm_prod.py       # Main training script
├── infer_lgbm.py             # Production inference
├── model_card_schema.json   # JSON Schema for cards
├── postproc/
│   └── calibration.py        # Platt, Isotonic, ECE
├── bench/
│   └── latency.py            # p50/p95/p99 benchmark
└── README_TRAINING.md        # This file

backend/data/
├── snapshots/
│   └── 2025-10-15T12-00-00Z/
│       ├── BTCUSDT.parquet
│       ├── manifest.json
│       └── ...
└── models/
    ├── 2025-10-15/
    │   ├── lgbm.pkl
    │   └── model_card.json
    ├── best_lgbm.pkl -> 2025-10-15/lgbm.pkl
    └── best_lgbm_model_card.json -> 2025-10-15/model_card.json
```

---

## Troubleshooting

### Issue: Snapshot checksum mismatch

```bash
# Re-create snapshot
rm -rf backend/data/snapshots/<date>
python backend/scripts/make_snapshot.py --days 90 --symbols BTCUSDT
```

### Issue: Schema validation failed

```bash
# Check which features are missing
python -c "
from backend.src.data.feature_registry.validator import FeatureSchemaValidator
validator = FeatureSchemaValidator('backend/src/data/feature_registry/features.yml')
print(validator.get_schema_info())
"
```

### Issue: Latency p95 > 80ms

- Check CPU load during benchmark
- Try smaller `num_leaves` (e.g., 32 instead of 64)
- Reduce model complexity with Optuna

### Issue: ECE > 0.1

- Try different calibration method (`sigmoid` vs `isotonic`)
- Check class balance (if severely imbalanced, use `scale_pos_weight`)
- Inspect calibration curve: `plot_calibration_curve(y_true, y_pred)`

---

## CI/CD Integration

### Backend CI Workflow (`.github/workflows/backend-ci.yml`)

```yaml
- name: Train LGBM (manual dispatch only)
  if: github.event_name == 'workflow_dispatch'
  run: |
    python -m backend.src.ml.train_lgbm_prod \
      --snapshot backend/data/snapshots/latest \
      --trials 50 \
      --calibration isotonic

- name: Validate Model Card
  run: |
    python -c "
    import json
    import jsonschema
    with open('backend/src/ml/model_card_schema.json') as f:
      schema = json.load(f)
    with open('backend/data/models/best_lgbm_model_card.json') as f:
      card = json.load(f)
    jsonschema.validate(card, schema)
    print('✅ Model card valid')
    "
```

---

## Next Steps (Gün 4-7)

- **Gün 4:** TFT production training (same snapshot)
- **Gün 5:** Backtest framework (90d, fees/slippage)
- **Gün 6:** Kill switch chaos testing
- **Gün 7:** 24h soak test + GO/NO-GO

---

**Last Updated:** 2025-10-15  
**Owner:** ML Team

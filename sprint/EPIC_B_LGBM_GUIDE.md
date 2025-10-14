# 📘 Epic-B: Production LGBM (Optuna + joblib)

**Sprint:** S10 - The Real Deal  
**Epic ID:** B  
**Owner:** @siyahkare  
**Status:** 🚧 In Progress

---

## 🎯 Amaç

- **Feature Store** (Parquet/DuckDB) ile **leak-safe** veri seti
- **Optuna** ile ≥200 deneme, early stopping
- **LightGBM (joblib)** production model
- **Model Card** ve **EnsemblePredictor** entegrasyonu

---

## 🏗️ Mimari

```
backend/src/data/
  feature_store.py         # Parquet/DuckDB + time-based split

backend/src/ml/
  train_lgbm_prod.py       # Optuna + LightGBM + joblib dump + model_card
  infer_lgbm.py            # Production inference wrapper

backend/data/
  feature_store/           # Parquet files per symbol
    BTCUSDT.parquet
  models/
    YYYY-MM-DD/
      lgbm.pkl
      model_card.json
    best_lgbm.pkl -> YYYY-MM-DD/lgbm.pkl
```

---

## ✅ Definition of Done (DoD)

- [ ] Leakage tests pass (no future leak)
- [ ] Val accuracy ≥ **65%**
- [ ] `backend/data/models/best_lgbm.pkl` and `model_card.json` created
- [ ] EnsemblePredictor loads real model
- [ ] CI gate: coverage ≥ **80%**, backtest KPI no regression

---

## 📝 Implementation

### 1) Feature Store — `backend/src/data/feature_store.py`

**Features:**
- Parquet append (schema evolution ready)
- Time-based train/val split (leak-safe)
- Minute-bar feature engineering
- Leakage guard assertions

**Core Functions:**
```python
def minute_features(bars: pd.DataFrame, horizon: int = 5) -> pd.DataFrame
def time_based_split(df: pd.DataFrame, val_days: int) -> Tuple[pd.DataFrame, pd.DataFrame]
def guard_no_future_leak(train: pd.DataFrame, val: pd.DataFrame)
def to_parquet(df: pd.DataFrame, out_dir: str, symbol: str) -> str
```

**Features Generated:**
- `ret1`: 1-period return
- `sma20_gap`: close - SMA(20)
- `sma50_gap`: close - SMA(50)
- `vol_z`: Volume z-score (50-period)
- Target `y`: 1 if price up in `horizon` minutes, else 0

### 2) Production Training — `backend/src/ml/train_lgbm_prod.py`

**Features:**
- Optuna hyperparameter search (≥200 trials)
- LightGBM binary classification
- Early stopping (100 rounds)
- Model card generation
- Symlink to `best_lgbm.pkl`

**Hyperparameters Tuned:**
- `learning_rate`: 0.01 - 0.2 (log scale)
- `num_leaves`: 16 - 256 (log scale)
- `min_data_in_leaf`: 16 - 512 (log scale)
- `feature_fraction`: 0.6 - 1.0
- `bagging_fraction`: 0.6 - 1.0
- `lambda_l1`, `lambda_l2`: 1e-9 - 10.0 (log scale)

**Output Artifacts:**
```
backend/data/models/YYYY-MM-DD/
  lgbm.pkl              # Trained model
  model_card.json       # Metadata (features, accuracy, timestamp)
backend/data/models/
  best_lgbm.pkl -> YYYY-MM-DD/lgbm.pkl  # Symlink
```

### 3) Inference Wrapper — `backend/src/ml/infer_lgbm.py`

**Features:**
- Thread-safe singleton model loader
- Lazy loading (load on first predict)
- Compatible with EnsemblePredictor interface

**Usage:**
```python
from backend.src.ml.infer_lgbm import LGBMProd

# Load once, reuse
proba = LGBMProd.predict_proba_up({
    "close": 100.0,
    "ret1": 0.01,
    "sma20_gap": -0.5,
    "sma50_gap": 1.2,
    "vol_z": 0.3
})
# Returns: 0.0 - 1.0 (probability of price going up)
```

### 4) EnsemblePredictor Integration

Update `backend/src/ml/models/ensemble_predictor.py`:

```python
from backend.src.ml.infer_lgbm import LGBMProd

class LGBMPredictor:
    def __init__(self, model_path: str = "backend/data/models/best_lgbm.pkl"):
        self.model_path = model_path
        self.loaded = False
    
    def load(self):
        if not self.loaded:
            LGBMProd.load(self.model_path)
            self.loaded = True
    
    def predict_proba(self, features: Dict[str, float]) -> float:
        return LGBMProd.predict_proba_up(features)
```

---

## 🧪 Tests

### Test 1: Leakage Guard — `backend/tests/test_feature_store_leakage.py`
- Verify time-based split has no future leak
- Assert `train.ts.max() < val.ts.min()`

### Test 2: Training Pipeline — `backend/tests/test_train_lgbm_prod_smoke.py`
- Synthetic data → feature store → train
- Verify artifacts created
- Verify symlink exists

### Test 3: Inference Wrapper — `backend/tests/test_infer_lgbm_wrapper.py`
- Load model (if exists)
- Predict with dummy features
- Assert output in [0.0, 1.0]

---

## ⚡ Quickstart

### Step 1: Install Dependencies

```bash
cd /Users/onur/levibot/backend
source venv/bin/activate
pip install lightgbm optuna pyarrow duckdb
```

### Step 2: Prepare Feature Store

```bash
python - <<'PY'
import pandas as pd
import json
from pathlib import Path
from backend.src.data.feature_store import minute_features, to_parquet

# Convert existing raw data to feature store
raw_files = list(Path("backend/data/raw").glob("BTCUSDT_*.json"))
if raw_files:
    rows = json.loads(raw_files[0].read_text())
    bars = pd.DataFrame(rows)[["ts","o","h","l","c","v"]]
    bars.columns = ["ts","open","high","low","close","volume"]
    
    df = minute_features(bars, horizon=5)
    path = to_parquet(df, symbol="BTCUSDT")
    print(f"✅ Feature store created: {path}")
    print(f"   Rows: {len(df)}, Features: {list(df.columns)}")
PY
```

### Step 3: Train Production Model

```bash
python - <<'PY'
from backend.src.ml.train_lgbm_prod import train_from_parquet

# Train with Optuna (50 trials for quick test, 200+ for production)
artifacts = train_from_parquet(
    "backend/data/feature_store/BTCUSDT.parquet",
    val_days=14,
    trials=50
)

print(f"✅ Model artifacts:")
for k, v in artifacts.items():
    print(f"   {k}: {v}")
PY
```

### Step 4: Verify Integration

```bash
# Check engine status (should load real LGBM)
curl -s http://localhost:8000/engines/status | jq

# Test inference
python - <<'PY'
from backend.src.ml.infer_lgbm import LGBMProd

proba = LGBMProd.predict_proba_up({
    "close": 100.0,
    "ret1": 0.01,
    "sma20_gap": -0.5,
    "sma50_gap": 1.2,
    "vol_z": 0.3
})
print(f"📊 Prediction: {proba:.4f} (probability of up move)")
PY
```

---

## 🚨 CI/CD Gates

### Requirements Update
```txt
# requirements.txt
lightgbm>=4.0.0
optuna>=3.0.0
pyarrow>=14.0.0
duckdb>=0.9.0
```

### GitHub Actions (`.github/workflows/ci.yml`)
```yaml
# Optional: CPU-intensive job on nightly schedule
# PR: 5-10 trials for quick validation
# Nightly: 200+ trials for production model
```

### Coverage Threshold
- Target: **≥80%**
- Upload `model_card.json` and `best_lgbm.pkl` as artifacts

---

## ⚠️ Risks & Mitigation

### 1. Data Leakage
**Risk:** Future data in training set  
**Mitigation:** 
- Time-based split only
- Lagged features (add `shift(1)` if needed)
- `guard_no_future_leak()` assertion in tests

### 2. Class Imbalance
**Risk:** Unbalanced binary target  
**Mitigation:**
- Monitor class distribution
- Use `is_unbalance=True` or `scale_pos_weight` in LGBM params

### 3. Optuna Timeout
**Risk:** Training takes too long  
**Mitigation:**
- Set `timeout` parameter in `study.optimize()`
- Or use fixed `n_trials` with progress bar

### 4. Model Versioning
**Risk:** Overwriting good models  
**Mitigation:**
- Dated directories (`YYYY-MM-DD/`)
- Symlink for `best_*`
- Model card tracks metadata

---

## 📊 Expected Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| Val Accuracy | ≥ 65% | Binary classification |
| Training Time | < 30 min | 200 trials on CPU |
| Inference Latency | < 10ms | CPU, single prediction |
| Model Size | < 50 MB | Joblib serialized |
| Feature Count | 5 | close, ret1, sma20_gap, sma50_gap, vol_z |

---

## 🔗 Next Steps

After Epic-B completion:

1. **Epic-C: Production TFT** - PyTorch Lightning transformer
2. **Epic-D: Backtesting** - 90-day historical simulation
3. **Model Monitoring** - Drift detection, auto-retraining
4. **Advanced Features** - Order flow, funding rate, on-chain data

---

**Status:** 🚧 Ready for implementation  
**Owner:** @siyahkare  
**Next:** Create skeleton files → Run training → Validate accuracy ≥65%


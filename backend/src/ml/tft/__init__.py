"""
Temporal Fusion Transformer (TFT) production module.

Components:
- train_tft_prod: Production training with PyTorch Lightning
- infer_tft: Thread-safe inference wrapper (singleton)
- drift: Drift detection (PSI, Jensen-Shannon)
"""

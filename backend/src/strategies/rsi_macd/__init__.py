"""
RSI + MACD Strategy Module
──────────────────────────
Combines RSI momentum and MACD trend for high-probability entries.

Modes:
  - scalp: 1m TF, tight SL/TP (1.2x ATR)
  - day: 15m TF, moderate targets (1.5x SL, 2x TP)
  - swing: 4h TF, wide targets (2x SL, 3x TP)

Entry Logic:
  1. MACD histogram crosses 0 (trend confirmation)
  2. RSI crosses 50 (momentum trigger)
  3. Conditions sync within N bars (2-3)
  4. Guards OK (spread/latency/vol)

Exit Logic:
  - MACD histogram reverses through 0
  - RSI crosses back through 50
  - ATR-based SL/TP hit
  - Timeout (bars held > max)
"""

from .config import RsiMacdConfig
from .engine import RsiMacdEngine

__all__ = ["RsiMacdConfig", "RsiMacdEngine"]

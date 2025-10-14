from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass


@dataclass
class RiskConfig:
    max_notional_usd: float = 1000.0
    cooldown_sec: int = 120
    atr_sl_mult: float = 1.5  # SL = price - atr*mult (buy)
    atr_tp_mult: float = 2.5  # TP = price + atr*mult (buy)
    fallback_sl_pct: float = 0.012  # ATR yoksa %1.2
    fallback_tp_pct: float = 0.020  # ATR yoksa %2.0


def atr_wilder(high: list[float], low: list[float], close: list[float], period: int = 14) -> float | None:
    """Wilder ATR hesaplama; n < period+1 ise None döner."""
    n = min(len(high), len(low), len(close))
    if n < period + 1:
        return None
    trs = []
    for i in range(1, n):
        tr = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
        trs.append(tr)
    # Wilder smoothing
    atr = sum(trs[:period]) / period
    for tr in trs[period:]:
        atr = (atr * (period - 1) + tr) / period
    return atr


@dataclass
class Policy:
    name: str
    atr_mult_sl: float
    atr_mult_tp: float
    cooldown_sec: int


POLICIES = {
    "conservative": Policy("conservative", atr_mult_sl=2.0, atr_mult_tp=1.0, cooldown_sec=45),
    "moderate":     Policy("moderate",     atr_mult_sl=1.5, atr_mult_tp=1.5, cooldown_sec=30),
    "aggressive":   Policy("aggressive",   atr_mult_sl=1.0, atr_mult_tp=2.0, cooldown_sec=20),
}

# --- Runtime cache (thread-safe) ---
_POLICY_LOCK = threading.Lock()
_CURRENT = (os.getenv("RISK_POLICY", "moderate") or "moderate").lower()


def _reset():
    global _CURRENT
    _CURRENT = (os.getenv("RISK_POLICY", "moderate") or "moderate").lower()


def list_policies() -> list[str]:
    return list(POLICIES.keys())


def get_policy_name() -> str:
    with _POLICY_LOCK:
        return _CURRENT


def set_policy_name(name: str) -> str:
    key = (name or "").lower().strip()
    if key not in POLICIES:
        raise ValueError(f"invalid policy: {name}")
    with _POLICY_LOCK:
        global _CURRENT
        _CURRENT = key
        return _CURRENT


def current_policy() -> Policy:
    with _POLICY_LOCK:
        name = _CURRENT
    return POLICIES.get(name, POLICIES["moderate"])


def clamp_notional(n: float) -> float:
    lo = float(os.getenv("RISK_MIN_NOTIONAL","5"))
    hi = float(os.getenv("RISK_MAX_NOTIONAL","250"))
    return max(lo, min(hi, float(n)))


def derive_sl_tp(side: str, price: float, atr: float, tp_hint=None, sl_hint=None):
    """
    Hints (FE'den) varsa önceliklidir. Yoksa policy+ATR ile türet.
    """
    pol = current_policy()
    # ATR multipliers
    m_sl = pol.atr_mult_sl * float(os.getenv("RISK_R_MULT","1.0"))
    m_tp = pol.atr_mult_tp * float(os.getenv("RISK_R_MULT","1.0"))

    if tp_hint is not None or sl_hint is not None:
        return sl_hint, tp_hint, {"policy": pol.name, "atr": atr, "source": "hint"}

    if side == "buy":
        sl = max(0.0, price - m_sl * atr)
        tp = price + m_tp * atr
    else:
        sl = price + m_sl * atr
        tp = max(0.0, price - m_tp * atr)

    return sl, tp, {"policy": pol.name, "atr": atr, "source": "atr"}


class RiskEngine:
    def __init__(self, cfg: RiskConfig):
        self.cfg = cfg
        self._last_ts: dict[str, float] = {}  # per-symbol cooldown

    def allow(self, symbol: str, notional: float, now: float | None = None) -> tuple[bool, str]:
        now = now or time.time()
        if notional > self.cfg.max_notional_usd:
            return False, "risk/max_notional"
        t0 = self._last_ts.get(symbol, 0.0)
        if now - t0 < self.cfg.cooldown_sec:
            return False, "risk/cooldown"
        return True, "ok"

    def record(self, symbol: str, when: float | None = None) -> None:
        self._last_ts[symbol] = when or time.time()

    def sl_tp(self, side: str, price: float, atr: float | None) -> tuple[float, float]:
        if atr and atr > 0:
            sl_off = atr * self.cfg.atr_sl_mult
            tp_off = atr * self.cfg.atr_tp_mult
        else:
            sl_off = price * self.cfg.fallback_sl_pct
            tp_off = price * self.cfg.fallback_tp_pct
        if side.lower() == "buy":
            return round(price - sl_off, 4), round(price + tp_off, 4)
        else:  # sell/short paper mantığı
            return round(price + sl_off, 4), round(price - tp_off, 4)




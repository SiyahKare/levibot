from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..infra.logger import log_event
from .precision import MarketMeta, passes_min_notional, quantize_amount


@dataclass
class RiskParams:
    equity_usd: float
    risk_per_trade: float  # 0.005 -> %0.5
    max_leverage: float
    max_pos_notional_pct: float | None = None  # 0.25 -> equity'nin %25'i
    max_pos_usd: float | None = None  # mutlak üst sınır
    hard_cap: float = 1.5  # pulse hard cap


def compute_stop_dist(
    entry: float, stop: float | None, atr: float | None, atr_k: float = 1.8
) -> float:
    if stop is not None:
        return abs(entry - float(stop))
    if atr is not None:
        return max(1e-9, float(atr_k) * float(atr))
    return max(1e-9, float(entry) * 0.008)


def size_with_pulse(
    symbol: str,
    side: str,
    entry: float,
    stop: float | None,
    atr: float | None,
    pulse_factor: float,
    risk: RiskParams,
    meta: MarketMeta,
    mark_price: float,
) -> dict[str, Any]:
    """
    Dönenler: {qty, base_qty, pulse_factor_applied, notional, guards:{...}, stop_dist}
    """
    stop_dist = compute_stop_dist(entry, stop, atr)

    base_qty = (risk.equity_usd * risk.risk_per_trade * risk.max_leverage) / stop_dist

    pf = max(1.0, min(float(pulse_factor or 1.0), float(risk.hard_cap)))
    qty = base_qty * pf

    notional = qty * float(mark_price)
    guards: dict[str, Any] = {}

    if risk.max_pos_notional_pct:
        cap = float(risk.equity_usd) * float(risk.max_pos_notional_pct)
        if notional > cap:
            guards["cap_pct"] = round(cap, 2)
            qty = cap / float(mark_price)
            notional = cap

    if risk.max_pos_usd:
        if notional > float(risk.max_pos_usd):
            guards["cap_abs"] = round(float(risk.max_pos_usd), 2)
            qty = float(risk.max_pos_usd) / float(mark_price)
            notional = float(risk.max_pos_usd)

    qty_q = quantize_amount(qty, meta)

    ok = passes_min_notional(entry, qty_q, meta)
    if not ok:
        need = float(meta.min_notional) / max(1e-9, float(entry))
        qty_q = quantize_amount(need, meta)
        notional = qty_q * float(mark_price)

    result = {
        "qty": qty_q,
        "base_qty": base_qty,
        "pulse_factor_applied": pf,
        "notional": notional,
        "guards": guards,
        "stop_dist": stop_dist,
    }
    log_event("SIZING", {"symbol": symbol, "side": side, **result})
    return result

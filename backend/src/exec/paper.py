from __future__ import annotations

import os

from ..infra.logger import log_event
from .types import PaperOrderRequest, PaperOrderResult


def _synthetic_mark(symbol: str) -> float:
    """Deterministik, offline mark fiyatı.

    Sembolden basit bir hash üreterek sabit bir fiyat türetir, ağ erişimi gerektirmez.
    """
    base = sum(ord(c) for c in symbol) % 100
    return 50.0 + float(base)


def place_paper_order(req: PaperOrderRequest) -> PaperOrderResult:
    mark = float(req.price) if req.price is not None else _synthetic_mark(req.symbol)
    qty = max(1e-6, req.notional_usd / max(mark, 1e-9))

    risk_enabled = os.getenv("PAPER_RISK_DISABLE", "false").lower() != "true"

    log_event(
        "ORDER_NEW",
        {"symbol": req.symbol, "side": req.side, "qty": qty, "price": mark},
        symbol=req.symbol,
        trace_id=req.trace_id,
    )
    log_event(
        "ORDER_FILLED",
        {"symbol": req.symbol, "side": req.side, "qty": qty, "price": mark},
        symbol=req.symbol,
        trace_id=req.trace_id,
    )

    log_event(
        "POSITION_CLOSED",
        {"symbol": req.symbol, "pnl_usdt": 0.0, "qty": qty},
        symbol=req.symbol,
        trace_id=req.trace_id,
    )

    return PaperOrderResult(
        ok=True,
        symbol=req.symbol,
        side=req.side,
        qty=qty,
        price=mark,
        filled=True,
        pnl_usd=0.0,
    )

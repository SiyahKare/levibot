from __future__ import annotations

import os

try:
    import ccxt  # type: ignore
except Exception:
    ccxt = None  # offline fallback

from ..core.risk import RiskConfig, RiskEngine, clamp_notional, derive_sl_tp
from ..infra.logger import log_event
from .types import PaperOrderResult

_risk = RiskEngine(RiskConfig())


def _synthetic_mark(symbol: str) -> float:
    """Offline deterministik fiyat: sembolden türet."""
    base = sum(ord(c) for c in symbol) % 100
    return 50.0 + float(base)


def _fetch_ticker_mark(exchange: str, symbol: str) -> float | None:
    """ccxt ile ticker fiyatını al; hata olursa None döndür."""
    if ccxt is None:
        return None
    try:
        ex = getattr(ccxt, exchange.lower())()
        t = ex.fetch_ticker(symbol)
        for k in ("last", "close", "bid", "ask"):
            v = t.get(k)
            if isinstance(v, (int, float)) and v > 0:
                return float(v)
    except Exception:
        return None
    return None


def place_cex_paper_order(
    exchange: str,
    symbol: str,  # ör: "ETH/USDT"
    side: str,  # "buy" | "sell"
    notional_usd: float,
    price: float | None = None,
    trace_id: str | None = None,
    fe: dict | None = None,
) -> PaperOrderResult:
    base_sym = symbol.replace("/", "")

    # Notional clamp
    notional = clamp_notional(notional_usd)

    risk_enabled = os.getenv("PAPER_RISK_DISABLE", "false").lower() != "true"
    ok, reason = (True, "ok") if not risk_enabled else _risk.allow(symbol, notional)
    if not ok:
        log_event(
            "ORDER_BLOCKED",
            {"reason": reason, "symbol": symbol, "side": side, "notional": notional},
            symbol=base_sym,
            trace_id=trace_id,
        )
        return PaperOrderResult(
            ok=False,
            symbol=symbol,
            side=side,
            qty=0.0,
            price=0.0,
            filled=False,
            pnl_usd=0.0,
        )

    mark = (
        float(price)
        if price is not None
        else (
            _fetch_ticker_mark(exchange, symbol)
            or _synthetic_mark(symbol.replace("/", ""))
        )
    )
    qty = max(1e-6, notional / max(mark, 1e-9))
    qty = float(f"{qty:.8f}")  # okunaklı

    log_event(
        "ORDER_NEW",
        {
            "exchange": exchange,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": mark,
            "notional": notional,
        },
        symbol=base_sym,
        trace_id=trace_id,
    )

    # Basit partial fill → %50 anında, %100 kapanış
    pf_qty = float(f"{qty * 0.5:.8f}")
    log_event(
        "ORDER_PARTIAL_FILL",
        {
            "exchange": exchange,
            "symbol": symbol,
            "side": side,
            "qty": pf_qty,
            "price": mark,
        },
        symbol=base_sym,
        trace_id=trace_id,
    )

    log_event(
        "ORDER_FILLED",
        {
            "exchange": exchange,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": mark,
        },
        symbol=base_sym,
        trace_id=trace_id,
    )

    # FE hint'leri (tp/sl) varsa al
    tp_hint = (fe or {}).get("tp", None)
    sl_hint = (fe or {}).get("sl", None)

    # ATR (yaklaşımı): ccxt ticker varsa high/low'dan kabaca; yoksa mark%1
    atr = max(0.001 * mark, abs(mark * 0.01))
    sl, tp, meta = derive_sl_tp(side, mark, atr, tp_hint, sl_hint)

    log_event(
        "RISK_SLTP",
        {
            "sl": sl,
            "tp": tp,
            "atr": meta.get("atr"),
            "policy": meta.get("policy"),
            "source": meta.get("source"),
        },
        symbol=base_sym,
        trace_id=trace_id,
    )

    # PnL = 0 (paper)
    log_event(
        "POSITION_CLOSED",
        {"exchange": exchange, "symbol": symbol, "pnl_usdt": 0.0, "qty": qty},
        symbol=base_sym,
        trace_id=trace_id,
    )

    if risk_enabled:
        _risk.record(symbol)

    return PaperOrderResult(
        ok=True, symbol=symbol, side=side, qty=qty, price=mark, filled=True, pnl_usd=0.0
    )

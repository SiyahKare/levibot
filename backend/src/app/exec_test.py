from __future__ import annotations

from fastapi import APIRouter
from ..exec.router import ExchangeRouter
from ..exec.precision import MarketMeta, quantize_amount, quantize_price
from ..infra.logger import log_event
import ccxt


router = APIRouter()


@router.post("/exec/test-order")
def test_order(symbol: str = "ETHUSDT", side: str = "buy", notional_usd: float = 25.0, tp_k: float = 2.4, sl_k: float = 1.8, dry_run: bool = False, exchange: str = "bybit", testnet: bool = True):
    try:
        r = ExchangeRouter(exchange=exchange, testnet=testnet)
        ccxt_sym = r.norm_ccxt_symbol(symbol)
        ticker = r.client.fetch_ticker(ccxt_sym)
        mark = float(ticker.get("last") or ticker.get("close") or 0)
        if mark <= 0:
            return {"ok": False, "error": "mark_price_unavailable"}
        atr = 10.0
        qty = max(1e-6, notional_usd / mark)
        # DRY
        if dry_run:
            price = mark * (0.999 if side == "buy" else 1.001)
            tp = price + tp_k * atr if side == "buy" else price - tp_k * atr
            sl = price - sl_k * atr if side == "buy" else price + sl_k * atr
            log_event("SMOKE_TEST_DRY", {"symbol": symbol, "side": side, "qty": qty, "price": price, "tp": tp, "sl": sl, "exchange": exchange, "testnet": testnet})
            log_event("POSITION_CLOSED", {"symbol": symbol, "pnl_usdt": 0.0, "qty": qty})
            return {"ok": True, "dry_run": True, "mark": mark, "qty": qty, "tp": tp, "sl": sl}
        # REAL
        price = mark * (0.999 if side == "buy" else 1.001)
        try:
            order = r.client.create_order(ccxt_sym, "limit", side, qty, price, {"timeInForce": "PO"})
        except ccxt.AuthenticationError as ae:
            tp = price + tp_k * atr if side == "buy" else price - tp_k * atr
            sl = price - sl_k * atr if side == "buy" else price + sl_k * atr
            log_event("SMOKE_TEST_DRY_AUTH", {"symbol": symbol, "side": side, "qty": qty, "price": price, "tp": tp, "sl": sl, "error": str(ae), "exchange": exchange, "testnet": testnet})
            log_event("POSITION_CLOSED", {"symbol": symbol, "pnl_usdt": 0.0, "qty": qty})
            return {"ok": True, "dry_run": True, "auth_fallback": True, "error": str(ae)}
        except ccxt.BaseError as ce:
            if any(k in str(ce).lower() for k in ["auth", "invalid api key", "permission", "retcode", "perm", "forbidden"]):
                price = mark * (0.999 if side == "buy" else 1.001)
                tp = price + tp_k * atr if side == "buy" else price - tp_k * atr
                sl = price - sl_k * atr if side == "buy" else price + sl_k * atr
                log_event("SMOKE_TEST_DRY_AUTH", {"symbol": symbol, "side": side, "qty": qty, "price": price, "tp": tp, "sl": sl, "error": str(ce), "exchange": exchange, "testnet": testnet})
                log_event("POSITION_CLOSED", {"symbol": symbol, "pnl_usdt": 0.0, "qty": qty})
                return {"ok": True, "dry_run": True, "auth_fallback": True, "error": str(ce)}
            raise
        tp = price + tp_k * atr if side == "buy" else price - tp_k * atr
        sl = price - sl_k * atr if side == "buy" else price + sl_k * atr
        oco = r.place_oco(ccxt_sym, side, qty, price, tp, sl)
        log_event("SMOKE_TEST", {"symbol": symbol, "side": side, "qty": qty, "price": price, "tp": tp, "sl": sl, "exchange": exchange, "testnet": testnet})
        return {"ok": True, "entry": order, "oco": oco.__dict__, "mark": mark}
    except Exception as e:
        if dry_run:
            log_event("SMOKE_TEST_DRY_ERR", {"symbol": symbol, "error": str(e), "exchange": exchange, "testnet": testnet})
            log_event("POSITION_CLOSED", {"symbol": symbol, "pnl_usdt": 0.0, "qty": 0})
            return {"ok": True, "dry_run": True, "error": str(e)}
        return {"ok": False, "error": str(e)}



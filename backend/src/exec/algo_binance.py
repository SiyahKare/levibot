import os
import requests
from .binance_sig import sign_params, auth_params
from ..infra.logger import log_event
from .algo_base import TWAPAdapter, register


BASE = "https://api.binance.com"


def _headers() -> dict:
    return {"X-MBX-APIKEY": os.environ.get("BINANCE_API_KEY", "")}


def twap_new_order(
    symbol: str,
    side: str,
    quantity: float,
    duration_sec: int,
    position_side: str | None = None,
    limit_price: float | None = None,
):
    body: dict = {"symbol": symbol, "side": side.upper(), "quantity": float(quantity), "duration": int(duration_sec)}
    if position_side:
        body["positionSide"] = position_side.upper()
    if limit_price is not None:
        body["limitPrice"] = float(limit_price)
    recv = int(os.getenv("BINANCE_RECV_WINDOW", "5000"))
    qp = sign_params(auth_params(body, recv), os.environ.get("BINANCE_API_SECRET", ""))
    url = f"{BASE}/sapi/v1/algo/futures/newOrderTwap?{qp}"
    r = requests.post(url, headers=_headers(), timeout=20)
    data = r.json()
    log_event("ORDER_NEW", {"mode": "native_twap", "req": body, "resp": data})
    r.raise_for_status()
    return data


def algo_open_orders():
    qp = sign_params(auth_params(), os.environ.get("BINANCE_API_SECRET", ""))
    url = f"{BASE}/sapi/v1/algo/futures/openOrders?{qp}"
    r = requests.get(url, headers=_headers(), timeout=10)
    data = r.json()
    log_event("ORDER_UPDATE", {"mode": "native_twap", "open": data})
    r.raise_for_status()
    return data


class BinanceTWAPAdapter(TWAPAdapter):
    name = "binance-native"

    def supports(self, symbol: str, notional: float, duration_sec: int) -> bool:
        if os.getenv("EXCHANGE", "").lower() != "binance":
            return False
        if notional < 1000:
            return False
        if not (300 <= duration_sec <= 86400):
            return False
        return True

    def place_twap(self, symbol: str, side: str, qty: float, duration_sec: int) -> dict:
        return twap_new_order(symbol, side, qty, duration_sec)


# Register adapter
register(BinanceTWAPAdapter())



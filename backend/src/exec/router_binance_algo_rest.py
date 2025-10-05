from __future__ import annotations

import os
import requests
from .binance_sig import sign_params, auth_params
from ..infra.logger import log_event


BASE = "https://api.binance.com"


def _server_timestamp() -> int:
    try:
        r = requests.get(f"{BASE}/api/v3/time", timeout=5)
        r.raise_for_status()
        return int(r.json().get("serverTime"))
    except Exception:
        # fallback to local time
        import time as _t
        return int(_t.time() * 1000)


def _headers() -> dict:
    key = os.environ.get("BINANCE_API_KEY") or os.environ.get("LEVI_ONUR_BINANCE_KEY")
    if not key:
        raise RuntimeError("BINANCE_API_KEY env missing")
    return {"X-MBX-APIKEY": key, "Content-Type": "application/x-www-form-urlencoded"}


def twap_new_order(
    symbol: str,
    side: str,
    quantity: float,
    duration_sec: int,
    position_side: str | None = None,
    limit_price: float | None = None,
) -> dict:
    body: dict = {
        "symbol": symbol,
        "side": side.upper(),
        "quantity": quantity,
        "duration": duration_sec,
    }
    if position_side:
        body["positionSide"] = position_side.upper()
    if limit_price:
        body["limitPrice"] = limit_price
    secret = os.environ.get("BINANCE_API_SECRET") or os.environ.get("LEVI_ONUR_BINANCE_SECRET", "")
    params = auth_params(body, int(os.getenv("BINANCE_RECV_WINDOW", "5000")))
    params["timestamp"] = _server_timestamp()
    qp = sign_params(params, secret)
    url = f"{BASE}/sapi/v1/algo/futures/newOrderTwap?{qp}"
    r = requests.post(url, headers=_headers(), timeout=20)
    data = r.json()
    log_event("ORDER_NEW", {"mode": "native_twap", "req": body, "resp": data})
    r.raise_for_status()
    return data


def algo_open_orders() -> dict:
    secret = os.environ.get("BINANCE_API_SECRET") or os.environ.get("LEVI_ONUR_BINANCE_SECRET", "")
    params = auth_params()
    params["timestamp"] = _server_timestamp()
    qp = sign_params(params, secret)
    url = f"{BASE}/sapi/v1/algo/futures/openOrders?{qp}"
    r = requests.get(url, headers=_headers(), timeout=10)
    data = r.json()
    log_event("ORDER_UPDATE", {"mode": "native_twap", "openOrders": data})
    r.raise_for_status()
    return data


def spot_account_info() -> dict:
    """Simple signed call to verify API key/secret work (Spot account endpoint)."""
    secret = os.environ.get("BINANCE_API_SECRET") or os.environ.get("LEVI_ONUR_BINANCE_SECRET", "")
    params = auth_params()
    params["timestamp"] = _server_timestamp()
    qp = sign_params(params, secret)
    url = f"{BASE}/api/v3/account?{qp}"
    r = requests.get(url, headers=_headers(), timeout=10)
    data = r.json()
    r.raise_for_status()
    return {"ok": True, "account_keys": list(data.keys())[:5]}



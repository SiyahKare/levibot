from __future__ import annotations

from fastapi import APIRouter, HTTPException
from ..exec.router_binance_algo_rest import twap_new_order, algo_open_orders, spot_account_info


router = APIRouter()


@router.post("/exec/algo-twap")
def exec_algo_twap(
    symbol: str,
    side: str,
    quantity: float,
    duration_sec: int = 900,
    position_side: str | None = None,
    limit_price: float | None = None,
):
    try:
        return twap_new_order(symbol, side, quantity, duration_sec, position_side, limit_price)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exec/algo-open-orders")
def exec_algo_open_orders():
    try:
        return algo_open_orders()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exec/binance-spot-account")
def exec_binance_spot_account():
    try:
        return spot_account_info()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



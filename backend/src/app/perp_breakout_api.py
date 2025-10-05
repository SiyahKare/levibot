from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from ..strategy.perp_breakout import BREAKOUT_REGISTRY, BreakoutParams


router = APIRouter()


class StartRequest(BaseModel):
    symbol: str = Field("BTCUSDT")
    exchange: str = Field("binance")
    testnet: bool = Field(True)
    dry_run: bool = Field(True)
    bar: str = Field("5m")
    lookback: int = Field(60)
    vol_ma_period: int = Field(20)
    max_leverage: int = Field(3)
    sl_pct: float = Field(0.015)
    tp_pct: float = Field(0.03)
    notional_usd: float = Field(50.0)


@router.post("/strategy/perp-breakout/start")
def start(req: StartRequest) -> dict:
    params = BreakoutParams(
        symbol=req.symbol,
        exchange=req.exchange,
        testnet=req.testnet,
        dry_run=req.dry_run,
        bar=req.bar,
        lookback=req.lookback,
        vol_ma_period=req.vol_ma_period,
        max_leverage=req.max_leverage,
        sl_pct=req.sl_pct,
        tp_pct=req.tp_pct,
        notional_usd=req.notional_usd,
    )
    tid = BREAKOUT_REGISTRY.start_task(params)
    return {"ok": True, "task_id": tid}


@router.post("/strategy/perp-breakout/stop")
def stop(task_id: str) -> dict:
    ok = BREAKOUT_REGISTRY.stop_task(task_id)
    return {"ok": bool(ok), "task_id": task_id}


@router.get("/strategy/perp-breakout/status")
def status(task_id: str | None = None) -> dict:
    return BREAKOUT_REGISTRY.status(task_id)


















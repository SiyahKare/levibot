from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field
from ..strategy.twap_rule_bot import TWAP_BOT_REGISTRY, TwapRuleParams


router = APIRouter()


class StartRequest(BaseModel):
    symbol: str = Field("ETHUSDT")
    exchange: str = Field("binance")
    testnet: bool = Field(True)
    dry_run: bool = Field(True)
    bar: str = Field("5m")
    target_pct: float = Field(0.01)
    stop_pct: float = Field(0.008)
    max_trades_per_day: int = Field(3)


@router.post("/strategy/twap-rule/start")
def start(req: StartRequest) -> dict:
    params = TwapRuleParams(
        symbol=req.symbol,
        exchange=req.exchange,
        testnet=req.testnet,
        dry_run=req.dry_run,
        bar=req.bar,
        target_pct=req.target_pct,
        stop_pct=req.stop_pct,
        max_trades_per_day=req.max_trades_per_day,
    )
    tid = TWAP_BOT_REGISTRY.start_task(params)
    return {"ok": True, "task_id": tid}


@router.post("/strategy/twap-rule/stop")
def stop(task_id: str) -> dict:
    ok = TWAP_BOT_REGISTRY.stop_task(task_id)
    return {"ok": bool(ok), "task_id": task_id}


@router.get("/strategy/twap-rule/status")
def status(task_id: str | None = None) -> dict:
    return TWAP_BOT_REGISTRY.status(task_id)


















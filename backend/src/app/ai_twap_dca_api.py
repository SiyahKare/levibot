from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..strategy.ai_twap_dca import REGISTRY, AiTwapDcaParams

router = APIRouter()


class StartRequest(BaseModel):
    symbol: str = Field("ETHUSDT")
    side: str = Field("buy")
    total_notional_usd: float = Field(50.0)
    num_slices: int = Field(6)
    interval_sec: int = Field(60)
    limit_offset_bps: int = Field(5)
    exchange: str = Field("binance")
    testnet: bool = Field(True)
    dry_run: bool = Field(True)
    max_slice_multiplier: float = Field(1.5)
    min_slice_multiplier: float = Field(0.5)


@router.post("/strategy/ai-twap-dca/start")
def start(req: StartRequest) -> dict:
    params = AiTwapDcaParams(
        symbol=req.symbol,
        side=req.side,  # type: ignore
        total_notional_usd=req.total_notional_usd,
        num_slices=req.num_slices,
        interval_sec=req.interval_sec,
        limit_offset_bps=req.limit_offset_bps,
        exchange=req.exchange,
        testnet=req.testnet,
        dry_run=req.dry_run,
        max_slice_multiplier=req.max_slice_multiplier,
        min_slice_multiplier=req.min_slice_multiplier,
    )
    task_id = REGISTRY.start_task(params)
    return {"ok": True, "task_id": task_id}


@router.post("/strategy/ai-twap-dca/cancel")
def cancel(task_id: str) -> dict:
    ok = REGISTRY.cancel_task(task_id)
    return {"ok": bool(ok), "task_id": task_id}


@router.get("/strategy/ai-twap-dca/status")
def status(task_id: str | None = None) -> dict:
    return REGISTRY.get_status(task_id)

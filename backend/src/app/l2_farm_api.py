from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..l2.farm import FARMER, REGISTRY

router = APIRouter()


@router.get("/l2/wallets")
def list_wallets() -> dict:
    return REGISTRY.list()


class SimReq(BaseModel):
    wallet_id: str = Field(...)
    network: str = Field("zksync")
    protocol: str = Field("syncswap")
    action: str = Field("swap")
    amount: float | None = Field(10.0)
    dry_run: bool = Field(True)
    extra: dict | None = Field(None)


@router.post("/l2/simulate")
def simulate(req: SimReq) -> dict:
    return FARMER.simulate_action(
        wallet_id=req.wallet_id,
        network=req.network,
        protocol=req.protocol,
        action=req.action,
        amount=req.amount,
        dry_run=req.dry_run,
        extra=req.extra,
    )


@router.post("/l2/run-sequence")
def run_sequence(
    wallet_id: str,
    network: str = "zksync",
    recipe: str = "default",
    dry_run: bool = True,
) -> dict:
    return FARMER.run_sequence(
        wallet_id=wallet_id, network=network, recipe=recipe, dry_run=dry_run
    )

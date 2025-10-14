from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    running: bool
    started_at: datetime | None = None
    open_positions: int = 0
    equity: float | None = None
    daily_dd_pct: float | None = None


class StartRequest(BaseModel):
    user_id: str | None = Field(None, description="Which user initiates the run")


class StopRequest(BaseModel):
    reason: str | None = None


class SetLeverageRequest(BaseModel):
    user_id: str
    leverage: int = Field(ge=1, le=50)


class ConfigSnapshot(BaseModel):
    users: dict
    risk: dict
    symbols: dict
    features: dict
    model: dict

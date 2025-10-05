from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ServiceStatus(BaseModel):
    running: bool
    started_at: Optional[datetime] = None
    open_positions: int = 0
    equity: Optional[float] = None
    daily_dd_pct: Optional[float] = None


class StartRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="Which user initiates the run")


class StopRequest(BaseModel):
    reason: Optional[str] = None


class SetLeverageRequest(BaseModel):
    user_id: str
    leverage: int = Field(ge=1, le=50)


class ConfigSnapshot(BaseModel):
    users: Dict
    risk: Dict
    symbols: Dict
    features: Dict
    model: Dict



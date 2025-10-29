from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, confloat, conint


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")  # Pydantic v2


class SMAParams(StrictModel):
    fast: int = Field(10, gt=0)
    slow: int = Field(50, gt=0)


class EMAParams(StrictModel):
    fast: int = Field(10, gt=0)
    slow: int = Field(50, gt=0)


class RSIParams(StrictModel):
    period: int = Field(14, gt=0)


PARAM_SCHEMAS = {
    "sma": SMAParams,
    "ema": EMAParams,
    "rsi": RSIParams,
}


class StrategyParams(BaseModel):
    fast: conint(gt=0) = 10
    slow: conint(gt=0) = 50


class SignalRunRequest(BaseModel):
    strategy: Literal["sma", "ema", "rsi"] = "sma"
    params: dict = {}  # Strategy-specific validation will happen in routes
    fee_bps: conint(ge=0, le=1000) = 10


class Metric(BaseModel):
    sharpe: float
    max_dd: float
    win_rate: confloat(ge=0, le=1)


class Order(BaseModel):
    pair: str
    side: Literal["BUY", "SELL"]
    qty: confloat(gt=0)
    kind: Literal["MARKET", "LIMIT"] = "MARKET"
    reason: str


class SignalRunResponse(BaseModel):
    equity_curve: list[float]
    orders: list[Order]
    metrics: Metric


class DryRunRequest(BaseModel):
    orders: list[Order]
    slippage_bps: conint(ge=0, le=2000) = 25


class Fill(BaseModel):
    pair: str
    side: Literal["BUY", "SELL"]
    qty: float
    price: float


class DryRunResponse(BaseModel):
    fills: list[Fill]
    pnl: float
    logs: list[str]


class SubmitRequest(BaseModel):
    orders: list[Order]
    network: Literal["base-sepolia", "anvil"] = "base-sepolia"


class SubmitResponse(BaseModel):
    tx_hash: str
    safe_tx_url: str | None = None
    orders_hash: str | None = None  # Audit trail
    request_id: str | None = None  # Request tracing

"""
Realtime data schemas.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class Tick(BaseModel):
    """Market tick data."""
    ts: float = Field(..., description="Unix timestamp")
    venue: str = Field(..., description="Exchange name (e.g., 'mexc')")
    symbol: str = Field(..., description="Normalized symbol (e.g., 'BTCUSDT')")
    last: float = Field(..., description="Last traded price")
    bid: float | None = Field(None, description="Best bid price")
    ask: float | None = Field(None, description="Best ask price")
    mark: float | None = Field(None, description="Mark price")
    volume: float | None = Field(None, description="24h volume")
    
    class Config:
        frozen = True


class Candle(BaseModel):
    """OHLCV candle."""
    ts: float
    symbol: str
    timeframe: str  # "1s", "1m", "5m", etc.
    open: float
    high: float
    low: float
    close: float
    volume: float


class Signal(BaseModel):
    """Trading signal from any source."""
    ts: float
    source: str  # "telegram", "ai", "strategy", etc.
    symbol: str
    side: str  # "buy" | "sell"
    size: float  # Quantity or notional
    sl: float | None = None
    tp: float | None = None
    confidence: float = 0.0
    rationale: str | None = None


class OrderFill(BaseModel):
    """Order fill event."""
    ts: float
    symbol: str
    side: str
    qty: float
    price: float
    fee: float
    is_paper: bool = True








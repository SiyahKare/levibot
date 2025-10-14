from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Side = Literal["buy", "sell"]


@dataclass
class PaperOrderRequest:
    symbol: str
    side: Side
    notional_usd: float
    price: float | None = None
    trace_id: str | None = None


@dataclass
class PaperOrderResult:
    ok: bool
    symbol: str
    side: Side
    qty: float
    price: float
    filled: bool
    pnl_usd: float

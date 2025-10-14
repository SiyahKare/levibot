from __future__ import annotations

from dataclasses import dataclass

from .router import ExchangeRouter, OrderResult


@dataclass
class OcoOrder:
    entry_id: str
    tp_id: str
    sl_id: str


class OCOManager:
    def __init__(self, router: ExchangeRouter) -> None:
        self.router = router

    def place(
        self, symbol: str, side: str, qty: float, entry: float, tp: float, sl: float
    ) -> OcoOrder:
        # Placeholder: single id emulation
        res: OrderResult = self.router.place_oco(symbol, side, qty, entry, tp, sl)
        return OcoOrder(entry_id=res.id, tp_id=f"{res.id}_tp", sl_id=f"{res.id}_sl")

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class TWAPAdapter(ABC):
    name: str = "base"

    @abstractmethod
    def supports(self, symbol: str, notional: float, duration_sec: int) -> bool:
        ...

    @abstractmethod
    def place_twap(self, symbol: str, side: str, qty: float, duration_sec: int) -> dict:
        ...


REGISTRY: List[TWAPAdapter] = []


def register(adapter: TWAPAdapter) -> None:
    REGISTRY.append(adapter)


def pick_twap_adapter(symbol: str, notional: float, duration_sec: int) -> Optional[TWAPAdapter]:
    for a in REGISTRY:
        try:
            if a.supports(symbol, notional, duration_sec):
                return a
        except Exception:
            continue
    return None

















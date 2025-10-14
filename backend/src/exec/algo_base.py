from __future__ import annotations

from abc import ABC, abstractmethod


class TWAPAdapter(ABC):
    name: str = "base"

    @abstractmethod
    def supports(self, symbol: str, notional: float, duration_sec: int) -> bool: ...

    @abstractmethod
    def place_twap(
        self, symbol: str, side: str, qty: float, duration_sec: int
    ) -> dict: ...


REGISTRY: list[TWAPAdapter] = []


def register(adapter: TWAPAdapter) -> None:
    REGISTRY.append(adapter)


def pick_twap_adapter(
    symbol: str, notional: float, duration_sec: int
) -> TWAPAdapter | None:
    for a in REGISTRY:
        try:
            if a.supports(symbol, notional, duration_sec):
                return a
        except Exception:
            continue
    return None

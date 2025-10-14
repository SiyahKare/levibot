from __future__ import annotations

from ..infra.logger import log_event
from .algo_base import TWAPAdapter, register


class BybitTWAPAdapter(TWAPAdapter):
    name = "bybit-native-stub"

    def supports(self, symbol: str, notional: float, duration_sec: int) -> bool:
        # Native TWAP uçları hesap/ürüne göre değişebilir; güvenli default: devre dışı
        return False

    def place_twap(self, symbol: str, side: str, qty: float, duration_sec: int) -> dict:
        log_event(
            "INFO",
            {"mode": "bybit-native", "msg": "stub adapter, fallback to software"},
        )
        raise NotImplementedError("Bybit native TWAP not enabled")


register(BybitTWAPAdapter())

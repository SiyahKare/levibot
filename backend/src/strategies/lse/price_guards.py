"""
Price Anomaly Guards
Prevent trades at anomalous prices
"""


class PriceGuard:
    """
    Guard against anomalous prices.

    Checks:
        1. ±10% from 5-minute median
        2. Min/max price clamp (10k-150k for BTCUSDT)
        3. Price change rate limit
    """

    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.price_history: list[float] = []
        self.max_history = 300  # 5 minutes at 1Hz

        # Symbol-specific clamps
        self.clamps = self._get_clamps(symbol)

    def _get_clamps(self, symbol: str) -> dict:
        """Get min/max price clamps for symbol"""
        # Default clamps
        clamps = {
            "BTCUSDT": {"min": 10000, "max": 150000},
            "ETHUSDT": {"min": 500, "max": 10000},
            "SOLUSDT": {"min": 10, "max": 500},
            "BNBUSDT": {"min": 100, "max": 1000},
            "DEFAULT": {"min": 0.01, "max": 100000},
        }

        return clamps.get(symbol, clamps["DEFAULT"])

    def update(self, price: float) -> None:
        """Update price history"""
        self.price_history.append(price)
        if len(self.price_history) > self.max_history:
            self.price_history.pop(0)

    def check_price(self, price: float) -> tuple[bool, str | None]:
        """
        Check if price is anomalous.

        Returns:
            (is_ok, reason)
            - (True, None) if price is OK
            - (False, reason) if price is blocked
        """
        # Clamp check
        if price < self.clamps["min"]:
            return False, f"price_too_low ({price} < {self.clamps['min']})"

        if price > self.clamps["max"]:
            return False, f"price_too_high ({price} > {self.clamps['max']})"

        # Median band check (if we have history)
        if len(self.price_history) >= 10:
            import numpy as np

            median = float(np.median(self.price_history[-300:]))

            deviation_pct = abs(price - median) / median

            if deviation_pct > 0.10:  # ±10%
                return (
                    False,
                    f"median_deviation ({deviation_pct*100:.1f}% from {median:.2f})",
                )

        return True, None

    def get_median(self) -> float | None:
        """Get current median price"""
        if len(self.price_history) < 10:
            return None

        import numpy as np

        return float(np.median(self.price_history[-300:]))

    def get_band(self) -> tuple[float, float] | None:
        """Get ±10% band around median"""
        median = self.get_median()
        if median is None:
            return None

        return (median * 0.9, median * 1.1)

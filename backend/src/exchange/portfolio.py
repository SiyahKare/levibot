"""Portfolio state: balances, positions, exposure tracking."""

from __future__ import annotations

import asyncio


class Portfolio:
    """
    Portfolio state manager: balances, positions, exposure.

    Syncs with exchange periodically to track:
        - Cash balances (USDT, etc.)
        - Open positions (qty, avg_px)
        - Notional exposure
    """

    def __init__(self):
        """Initialize empty portfolio."""
        self.balances: dict[str, float] = {}
        self.positions: dict[str, dict[str, float]] = {}  # symbol -> {qty, avg_px}

    async def refresh(self):
        """
        Refresh balances and positions from exchange.

        TODO:
            - Real exchange API call (e.g., GET /api/v3/account)
            - Parse balances and positions
            - Handle API errors gracefully
        """
        # Placeholder: initialize with default values
        self.balances = {"USDT": 10_000.0}

        # Ensure all tracked symbols have position entries
        for symbol in list(self.positions.keys()):
            self.positions.setdefault(symbol, {"qty": 0.0, "avg_px": 0.0})

    def exposure_notional(self, symbol: str, last_price: float) -> float:
        """
        Calculate notional exposure for a symbol.

        Args:
            symbol: Trading symbol
            last_price: Current market price

        Returns:
            Absolute notional value (|qty × price|)
        """
        pos = self.positions.get(symbol, {"qty": 0.0})
        return abs(pos["qty"] * last_price)

    def get_balance(self, asset: str) -> float:
        """
        Get balance for an asset.

        Args:
            asset: Asset symbol (e.g., "USDT")

        Returns:
            Balance amount
        """
        return self.balances.get(asset, 0.0)

    def get_position(self, symbol: str) -> dict[str, float]:
        """
        Get position details for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position dict with keys: qty, avg_px
        """
        return self.positions.get(symbol, {"qty": 0.0, "avg_px": 0.0})


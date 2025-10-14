"""
Slippage and fee calculations for realistic paper trading.
"""

from __future__ import annotations

from ..infra.settings import settings


def slippage_price(mark: float, side: str, qty: float = 0.0) -> float:
    """
    Calculate fill price with slippage.

    Args:
        mark: Current market price
        side: "buy" or "sell"
        qty: Order quantity (for size-based slippage, optional)

    Returns:
        Adjusted fill price including slippage
    """
    slippage_adj = mark * (settings.SLIPPAGE_BPS / 10000.0)

    if side.lower() == "buy":
        # Buy at slightly higher price (adverse movement)
        return mark + slippage_adj
    else:
        # Sell at slightly lower price
        return mark - slippage_adj


def calculate_fee(notional: float, is_maker: bool = False) -> float:
    """
    Calculate trading fee.

    Args:
        notional: Notional value (price * quantity)
        is_maker: Whether order is maker (lower fee) or taker

    Returns:
        Fee amount in USD
    """
    fee_bps = settings.FEE_MAKER_BPS if is_maker else settings.FEE_TAKER_BPS
    return abs(notional) * (fee_bps / 10000.0)

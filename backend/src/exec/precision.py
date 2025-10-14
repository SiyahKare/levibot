from __future__ import annotations

from decimal import ROUND_DOWN, Decimal


class MarketMeta:
    def __init__(self, m: dict):
        self.price_step = Decimal(
            str(m.get("precision", {}).get("price", m.get("priceIncrement", "0.01")))
        )
        self.amount_step = Decimal(
            str(m.get("precision", {}).get("amount", m.get("amountIncrement", "0.001")))
        )
        self.min_notional = Decimal(
            str(m.get("limits", {}).get("cost", {}).get("min", 0))
        )
        self.min_amt = Decimal(str(m.get("limits", {}).get("amount", {}).get("min", 0)))
        self.min_price = Decimal(
            str(m.get("limits", {}).get("price", {}).get("min", 0))
        )


def _round_step(x: Decimal, step: Decimal) -> Decimal:
    q = (x / step).to_integral_value(rounding=ROUND_DOWN)
    return q * step


def quantize_price(price: float, meta: MarketMeta) -> float:
    p = _round_step(Decimal(str(price)), meta.price_step)
    if p < meta.min_price:
        p = meta.min_price
    return float(p)


def quantize_amount(amount: float, meta: MarketMeta) -> float:
    a = _round_step(Decimal(str(amount)), meta.amount_step)
    if a < meta.min_amt:
        a = meta.min_amt
    return float(a)


def passes_min_notional(price: float, amount: float, meta: MarketMeta) -> bool:
    notional = Decimal(str(price)) * Decimal(str(amount))
    return notional >= meta.min_notional

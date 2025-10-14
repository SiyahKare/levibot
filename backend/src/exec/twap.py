import asyncio

from ..infra.logger import log_event
from .precision import MarketMeta, quantize_price
from .router import ExchangeRouter


async def twap_software(
    ccxt_symbol: str,
    side: str,
    qty: float,
    duration_sec: int,
    slices: int,
    meta: MarketMeta,
):
    ex = ExchangeRouter()
    sleep_s = max(1, duration_sec // max(1, slices))
    per_slice = qty / max(1, slices)
    for i in range(slices):
        try:
            ticker = ex.client.fetch_ticker(ccxt_symbol)
            mark = float(ticker.get("last") or ticker.get("close"))
            px = quantize_price(mark * (0.9997 if side == "buy" else 1.0003), meta)
            ex.client.create_order(
                ccxt_symbol, "limit", side, per_slice, px, {"timeInForce": "PO"}
            )
            log_event(
                "TWAP_SLICE",
                {
                    "symbol": ccxt_symbol,
                    "i": i + 1,
                    "n": slices,
                    "side": side,
                    "px": px,
                    "qty": per_slice,
                },
            )
        except Exception as e:
            log_event("ERROR", {"scope": "twap_soft_slice", "err": str(e)})
        await asyncio.sleep(sleep_s)


def start_twap_software(
    ccxt_symbol: str,
    side: str,
    qty: float,
    duration_sec: int,
    slices: int,
    meta: MarketMeta,
):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            twap_software(ccxt_symbol, side, qty, duration_sec, slices, meta)
        )
    except RuntimeError:
        asyncio.run(twap_software(ccxt_symbol, side, qty, duration_sec, slices, meta))

import json
import time
from contextvars import ContextVar

from .schemas import Order

request_context: ContextVar[str] = ContextVar("request_id", default="")

MAX_POS_USD = 5000
ALLOWED = {"BTCUSDT", "ETHUSDT"}
JSONL = "artifacts/risk_veto.jsonl"


def _coerce(o: Order | dict) -> Order:
    return o if isinstance(o, Order) else Order(**o)


def _log(event: dict, route: str = "/signals/run"):
    from pathlib import Path

    Path(JSONL).parent.mkdir(parents=True, exist_ok=True)
    event["ts"] = time.time()
    event["rid"] = request_context.get("")
    event["route"] = route
    with open(JSONL, "a") as f:
        f.write(json.dumps(event) + "\n")


def evaluate_and_filter(orders_in: list[Order | dict]) -> tuple[list[Order], list[str]]:
    orders, logs, pos_usd = [], [], 0.0
    for _o in orders_in:
        o = _coerce(_o)
        if o.pair not in ALLOWED:
            msg = f"REJECT allowed_pairs: {o.pair}"
            logs.append(msg)
            _log(
                {
                    "event": "REJECT",
                    "rule": "allowed_pairs",
                    "order": o.dict(),
                    "reason": msg,
                }
            )
            continue
        # kaba USD tahmin; gerçek fiyat feed'i yok
        est_usd = 100.0 * o.qty
        if pos_usd + est_usd > MAX_POS_USD:
            msg = f"REJECT max_position_usd: {pos_usd+est_usd}>{MAX_POS_USD}"
            logs.append(msg)
            _log(
                {
                    "event": "REJECT",
                    "rule": "max_position_usd",
                    "order": o.dict(),
                    "reason": msg,
                }
            )
            continue
        pos_usd += est_usd
        orders.append(o)
    return orders, logs

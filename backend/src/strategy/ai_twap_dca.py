from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Literal

from ..exec.router import ExchangeRouter
from ..infra.logger import JsonlEventLogger


Side = Literal["buy", "sell"]


@dataclass
class AiTwapDcaParams:
    symbol: str
    side: Side
    total_notional_usd: float
    num_slices: int
    interval_sec: int
    limit_offset_bps: int = 0
    exchange: str = "bybit"
    testnet: bool = True
    dry_run: bool = True
    max_slice_multiplier: float = 1.5  # bias ile slice genişleme sınırı
    min_slice_multiplier: float = 0.5  # bias ile slice daralma sınırı


@dataclass
class AiTwapDcaStatus:
    task_id: str
    params: AiTwapDcaParams
    started_at: float
    finished_at: Optional[float]
    cancelled: bool
    slices_total: int
    slices_done: int
    last_error: Optional[str]


class AiTwapDcaTask:
    def __init__(self, task_id: str, params: AiTwapDcaParams) -> None:
        self.task_id = task_id
        self.params = params
        self.started_at = time.time()
        self.finished_at: Optional[float] = None
        self.cancelled = False
        self.slices_total = params.num_slices
        self.slices_done = 0
        self.last_error: Optional[str] = None
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def status(self) -> AiTwapDcaStatus:
        return AiTwapDcaStatus(
            task_id=self.task_id,
            params=self.params,
            started_at=self.started_at,
            finished_at=self.finished_at,
            cancelled=self.cancelled,
            slices_total=self.slices_total,
            slices_done=self.slices_done,
            last_error=self.last_error,
        )

    def cancel(self) -> None:
        with self._lock:
            self.cancelled = True

    def start(self, logger: JsonlEventLogger) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run() -> None:
            logger.write("AI_TWAP_START", {"task_id": self.task_id, "params": asdict(self.params)})
            try:
                router = ExchangeRouter(exchange=self.params.exchange, testnet=self.params.testnet)
            except Exception as e:
                self.last_error = str(e)
                logger.write("AI_TWAP_ERR", {"task_id": self.task_id, "stage": "init", "error": str(e)})
                self.finished_at = time.time()
                return

            per_slice = max(1e-6, self.params.total_notional_usd / max(1, self.params.num_slices))

            for i in range(self.params.num_slices):
                with self._lock:
                    if self.cancelled:
                        logger.write("AI_TWAP_CANCELLED", {"task_id": self.task_id, "slices_done": self.slices_done})
                        self.finished_at = time.time()
                        return
                try:
                    # Fetch mark
                    ccxt_sym = router.norm_ccxt_symbol(self.params.symbol)
                    ticker = router.client.fetch_ticker(ccxt_sym)
                    mark = float(ticker.get("last") or ticker.get("close") or 0.0)
                    if mark <= 0:
                        raise RuntimeError("mark_price_unavailable")

                    # Simple bias: son 1-2 reading momentum, -1..+1
                    momentum = 0.0
                    try:
                        bid = float(ticker.get("bid") or mark)
                        ask = float(ticker.get("ask") or mark)
                        mid = 0.5 * (bid + ask)
                        momentum = max(-1.0, min(1.0, (mark - mid) / max(1e-9, mid) * 50))  # ~bps ölçekli
                    except Exception:
                        momentum = 0.0

                    # Adjust slice by bias
                    mult = 1.0 + 0.5 * momentum if self.params.side == "buy" else 1.0 - 0.5 * momentum
                    mult = max(self.params.min_slice_multiplier, min(self.params.max_slice_multiplier, mult))
                    slice_notional = per_slice * mult
                    qty = max(1e-9, slice_notional / mark)

                    # Limit offset
                    px_off = self.params.limit_offset_bps / 10000.0
                    price = mark * (1.0 - px_off) if self.params.side == "buy" else mark * (1.0 + px_off)

                    if self.params.dry_run:
                        logger.write("AI_TWAP_SLICE", {
                            "task_id": self.task_id,
                            "i": i + 1,
                            "symbol": self.params.symbol,
                            "side": self.params.side,
                            "mark": mark,
                            "price": price,
                            "qty": qty,
                            "notional": slice_notional,
                            "momentum": momentum,
                            "dry": True,
                        })
                    else:
                        try:
                            order = router.client.create_order(ccxt_sym, "limit", self.params.side, qty, price, {"timeInForce": "PO"})
                            logger.write("AI_TWAP_SLICE", {
                                "task_id": self.task_id,
                                "i": i + 1,
                                "symbol": self.params.symbol,
                                "side": self.params.side,
                                "mark": mark,
                                "price": price,
                                "qty": qty,
                                "notional": slice_notional,
                                "momentum": momentum,
                                "dry": False,
                                "order_id": str(order.get("id")),
                            })
                        except Exception as e:
                            # Fallback to dry-run and continue
                            self.last_error = str(e)
                            logger.write("AI_TWAP_SLICE", {
                                "task_id": self.task_id,
                                "i": i + 1,
                                "symbol": self.params.symbol,
                                "side": self.params.side,
                                "mark": mark,
                                "price": price,
                                "qty": qty,
                                "notional": slice_notional,
                                "momentum": momentum,
                                "dry": True,
                                "error": str(e),
                            })

                    self.slices_done += 1
                    if i < self.params.num_slices - 1:
                        time.sleep(self.params.interval_sec)
                except Exception as e:
                    self.last_error = str(e)
                    logger.write("AI_TWAP_ERR", {"task_id": self.task_id, "stage": "slice", "i": i + 1, "error": str(e)})
                    time.sleep(self.params.interval_sec)

            self.finished_at = time.time()
            logger.write("AI_TWAP_DONE", {"task_id": self.task_id, "slices_done": self.slices_done})

        self._thread = threading.Thread(target=_run, name=f"ai-twap-dca-{self.task_id}", daemon=True)
        self._thread.start()


class AiTwapDcaRegistry:
    def __init__(self) -> None:
        self._tasks: Dict[str, AiTwapDcaTask] = {}
        self._lock = threading.Lock()
        self._logger = JsonlEventLogger()

    def start_task(self, params: AiTwapDcaParams) -> str:
        task_id = uuid.uuid4().hex[:12]
        task = AiTwapDcaTask(task_id, params)
        with self._lock:
            self._tasks[task_id] = task
        task.start(self._logger)
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            t = self._tasks.get(task_id)
        if not t:
            return False
        t.cancel()
        return True

    def get_status(self, task_id: Optional[str] = None) -> Dict[str, dict]:
        with self._lock:
            items = list(self._tasks.items())
        if task_id:
            t = dict(items).get(task_id)
            return {task_id: asdict(t.status())} if t else {}
        return {k: asdict(v.status()) for k, v in items}


REGISTRY = AiTwapDcaRegistry()


















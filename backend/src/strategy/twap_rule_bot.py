from __future__ import annotations

import datetime as dt

import duckdb as d

from ..exec.algo_base import pick_twap_adapter
from ..exec.precision import MarketMeta
from ..exec.router import ExchangeRouter
from ..exec.sizing import RiskParams, size_with_pulse
from ..exec.twap import start_twap_software
from ..infra.config_store import load as load_cfg
from ..infra.logger import JsonlEventLogger, log_event
from ..signals.hybrid import combine_signals

_last_at = {}


def _now():
    return dt.datetime.utcnow()


def _cooldown_ok(key: str, min_: int) -> bool:
    t = _last_at.get(key)
    return (t is None) or (_now() - t >= dt.timedelta(minutes=min_))


def _spread_bps(ex: ExchangeRouter, cc: str):
    ob = ex.client.fetch_order_book(cc, limit=5)
    bid = float(ob["bids"][0][0])
    ask = float(ob["asks"][0][0])
    return (ask - bid) / ((ask + bid) / 2) * 1e4, bid, ask


def run_tick(user_id: str = "default") -> None:
    cfg = load_cfg().get("twap_rule_bot") or {}
    if not cfg.get("enabled", False):
        return
    tf = cfg.get("timeframe", "1m")
    cooldown = int(cfg.get("cooldown_min", 10))
    thrL = float(cfg.get("thr_long", 0.58))
    thrS = float(cfg.get("thr_short", 0.42))
    min_spread = float(cfg.get("min_spread_bps", 2.0))
    duration = int(cfg.get("duration_sec", 900))
    slices = int(cfg.get("slices", 30))
    mode = (cfg.get("mode", "auto") or "auto").lower()

    ex = ExchangeRouter()
    try:
        ex.client.load_markets()
    except Exception:
        pass

    rc = load_cfg().get("risk", {})
    equity = float(load_cfg().get("runtime", {}).get("equity_usd", 1000))
    rp = RiskParams(
        equity_usd=equity,
        risk_per_trade=float(rc.get("risk_per_trade_pct", 0.5)) / 100.0,
        max_leverage=float(rc.get("max_leverage", 3)),
        max_pos_notional_pct=(float(rc.get("max_pos_notional_pct", 0)) / 100.0 or None),
        max_pos_usd=(float(rc.get("max_pos_usd", 0)) or None),
        hard_cap=float(
            load_cfg()
            .get("telegram", {})
            .get("evaluation", {})
            .get("pulse", {})
            .get("hard_cap", 1.5)
        ),
    )

    for symbol in cfg.get("symbols", ["ETHUSDT"]):
        cc = ex.norm_ccxt_symbol(symbol)
        meta = MarketMeta(ex.client.markets.get(cc, {}))

        sp_bps, bid, ask = _spread_bps(ex, cc)
        if sp_bps > min_spread:
            continue

        import polars as pl

        mark = float(ex.client.fetch_ticker(cc).get("last"))
        df = pl.DataFrame({"close": [mark], "symbol": [symbol]})
        hsig = combine_signals(df, ml_proba=0.5, news_bias=0.0)
        pL = max(0.0, min(1.0, 0.5 + hsig.score))
        pS = 1.0 - pL
        if cfg.get("trend_required", True) and max(pL, pS) < max(thrL, 1 - thrS):
            continue

        side = (
            "buy"
            if pL >= thrL and _cooldown_ok(symbol + ":L", cooldown)
            else (
                "sell"
                if pS >= (1 - thrS) and _cooldown_ok(symbol + ":S", cooldown)
                else None
            )
        )
        if not side:
            continue

        # ATR kısa pencere tahmini
        bars = d.sql(
            f"SELECT close, high, low FROM read_parquet('backend/data/parquet/ohlcv/{symbol}_{tf}.parquet') ORDER BY time DESC LIMIT 45"
        ).df()
        atr = None
        if not bars.empty:
            import numpy as np

            c = bars["close"].to_numpy()
            h_ = bars["high"].to_numpy()
            l_ = bars["low"].to_numpy()
            prev = np.roll(c, 1)
            prev[0] = c[0]
            tr = np.maximum(h_ - l_, np.maximum(abs(h_ - prev), abs(l_ - prev)))
            atr = float(tr[-14:].mean())

        entry = mark
        stop = (
            (entry - 1.8 * atr)
            if (atr and side == "buy")
            else (entry + 1.8 * atr) if atr else None
        )

        pulse_factor = (hsig.components.get("telegram_pulse", {}) or {}).get(
            "factor", 1.0
        )
        sizing = size_with_pulse(
            symbol, side, entry, stop, atr, pulse_factor, rp, meta, mark_price=mark
        )
        qty = sizing.get("qty", 0.0)
        if qty <= 0:
            continue

        notional = qty * mark
        adapter = (
            pick_twap_adapter(symbol, notional, duration)
            if mode in ("native", "auto")
            else None
        )
        if adapter:
            try:
                adapter.place_twap(
                    symbol, "BUY" if side == "buy" else "SELL", qty, duration
                )
                _last_at[symbol + (":L" if side == "buy" else ":S")] = _now()
                log_event(
                    "STRAT_TWAP_OPEN",
                    {
                        "symbol": symbol,
                        "side": side,
                        "qty": qty,
                        "duration": duration,
                        "mode": adapter.name,
                        "pulse": pulse_factor,
                        "spread_bps": sp_bps,
                    },
                )
                continue
            except Exception as e:
                log_event(
                    "ERROR",
                    {
                        "scope": "twap_native",
                        "adapter": getattr(adapter, "name", "?"),
                        "symbol": symbol,
                        "err": str(e),
                    },
                )
        start_twap_software(cc, side, qty, duration, slices, meta)
        _last_at[symbol + (":L" if side == "buy" else ":S")] = _now()
        log_event(
            "STRAT_TWAP_OPEN",
            {
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "duration": duration,
                "mode": "software",
                "pulse": pulse_factor,
                "spread_bps": sp_bps,
            },
        )


import threading
import uuid

# --- Minimal API Registry (stub) for twap_rule_api ---
from dataclasses import dataclass


@dataclass
class TwapRuleParams:
    symbol: str = "ETHUSDT"
    exchange: str = "binance"
    testnet: bool = True
    dry_run: bool = True
    bar: str = "5m"
    target_pct: float = 0.01
    stop_pct: float = 0.008
    max_trades_per_day: int = 3


class _TwapRuleTask:
    def __init__(self, task_id: str, params: TwapRuleParams) -> None:
        self.id = task_id
        self.params = params
        self.stopped = False
        self.logger = JsonlEventLogger()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _loop() -> None:
            self.logger.write(
                "TWAP_RULE_START", {"task_id": self.id, "params": self.params.__dict__}
            )
            try:
                while not self.stopped:
                    try:
                        run_tick(user_id="default")
                    except Exception as e:
                        self.logger.write(
                            "TWAP_RULE_ERR", {"task_id": self.id, "error": str(e)}
                        )
                    # basic cadence ~60s
                    for _ in range(60):
                        if self.stopped:
                            break
                        dt.time.sleep(1)
            finally:
                self.logger.write("TWAP_RULE_STOP", {"task_id": self.id})

        self._thread = threading.Thread(
            target=_loop, name=f"twap-rule-{self.id}", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self.stopped = True


class TwapRuleRegistry:
    def __init__(self) -> None:
        self._tasks: dict[str, _TwapRuleTask] = {}

    def start_task(self, params: TwapRuleParams) -> str:
        tid = uuid.uuid4().hex[:12]
        t = _TwapRuleTask(tid, params)
        self._tasks[tid] = t
        t.start()
        return tid

    def stop_task(self, task_id: str) -> bool:
        t = self._tasks.get(task_id)
        if not t:
            return False
        t.stop()
        return True

    def status(self, task_id: str | None = None) -> dict[str, dict]:
        if task_id:
            t = self._tasks.get(task_id)
            if not t:
                return {}
            return {task_id: {"stopped": t.stopped, "params": t.params.__dict__}}
        return {
            k: {"stopped": v.stopped, "params": v.params.__dict__}
            for k, v in self._tasks.items()
        }


TWAP_BOT_REGISTRY = TwapRuleRegistry()

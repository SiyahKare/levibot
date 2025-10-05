from __future__ import annotations

import datetime as dt
from typing import Dict, Optional
import duckdb as d
from ..infra.logger import log_event
from ..signals.hybrid import combine_signals
from ..exec.router import ExchangeRouter
from ..exec.precision import MarketMeta, quantize_price
from ..exec.sizing import size_with_pulse, RiskParams
from ..infra.config_store import load as load_cfg


_last_trade_at: Dict[str, dt.datetime] = {}


def _now_utc() -> dt.datetime:
    return dt.datetime.utcnow()


def _cooldown_ok(symbol_key: str, minutes: int) -> bool:
    t = _last_trade_at.get(symbol_key)
    return (t is None) or (_now_utc() - t >= dt.timedelta(minutes=minutes))


def _mark_and_atr(symbol: str, timeframe: str, lookback_min: int):
    ex = ExchangeRouter()
    cc = ex.norm_ccxt_symbol(symbol)
    ticker = ex.client.fetch_ticker(cc)
    mark = float(ticker.get("last") or ticker.get("close"))
    end = _now_utc()
    start = end - dt.timedelta(minutes=lookback_min + 5)
    path = f"backend/data/parquet/ohlcv/{symbol}_{timeframe}.parquet"
    bars = d.sql(
        f"""
        SELECT time, open, high, low, close FROM read_parquet('{path}')
        WHERE time BETWEEN TIMESTAMP '{start:%Y-%m-%d %H:%M:%S}' AND TIMESTAMP '{end:%Y-%m-%d %H:%M:%S}'
        ORDER BY time
        """
    ).df()
    if bars.empty:
        return mark, None, None
    import numpy as np
    high = bars["high"].to_numpy(); low = bars["low"].to_numpy(); close = bars["close"].to_numpy()
    prev_close = np.roll(close, 1); prev_close[0] = close[0]
    tr = np.maximum(high - low, np.maximum(abs(high - prev_close), abs(low - prev_close)))
    n = min(14, len(tr))
    atr = float(np.mean(tr[-n:]))
    rng_hi = float(high[-(lookback_min or 30):].max())
    rng_lo = float(low[-(lookback_min or 30):].min())
    return mark, atr, (rng_hi, rng_lo)


def _risk_params(user_id: str) -> RiskParams:
    cfg = load_cfg()
    r = cfg.get("risk", {})
    equity = float(cfg.get("runtime", {}).get("equity_usd", 1000))
    return RiskParams(
        equity_usd=equity,
        risk_per_trade=float(r.get("risk_per_trade_pct", 0.5)) / 100.0,
        max_leverage=float(r.get("max_leverage", 3)),
        max_pos_notional_pct=(float(r.get("max_pos_notional_pct", 0)) / 100.0 or None),
        max_pos_usd=(float(r.get("max_pos_usd", 0)) or None),
        hard_cap=float(cfg.get("telegram", {}).get("evaluation", {}).get("pulse", {}).get("hard_cap", 1.5)),
    )


def run_tick(user_id: str = "default") -> None:
    cfg = load_cfg().get("perp_breakout") or load_cfg().get("strategy", {}).get("perp_breakout", {})
    if not cfg or not cfg.get("enabled", True):
        return
    timeframe = cfg.get("timeframe", "1m")
    lookback_min = int(cfg.get("lookback_min", 45))
    entry_off = float(cfg.get("entry_offset_bps", 3)) / 10000.0
    thr_long = float(cfg.get("thr_long", 0.58))
    thr_short = float(cfg.get("thr_short", 0.42))
    cooldown = int(cfg.get("cooldown_min", 15))

    ex = ExchangeRouter()
    try:
        ex.client.load_markets()
    except Exception:
        pass

    for symbol in cfg.get("symbols", ["ETHUSDT"]):
        mark, atr, rng = _mark_and_atr(symbol, timeframe, lookback_min)
        if rng is None:
            continue
        rng_hi, rng_lo = rng

        # Basit veri çerçevesi: burada sadece side/strength/close taşıyan minimal DF ile baseline hesaplanabilir.
        import polars as pl
        df = pl.DataFrame({"close": [mark], "symbol": [symbol]})
        decision_sig = combine_signals(df, ml_proba=0.5, news_bias=0.0)
        pL = max(0.0, min(1.0, 0.5 + decision_sig.score))
        pS = 1.0 - pL

        go_long = (mark >= rng_hi) and (pL >= thr_long) and _cooldown_ok(symbol + ":LONG", cooldown)
        go_short = (mark <= rng_lo) and (pS >= (1 - thr_short)) and _cooldown_ok(symbol + ":SHORT", cooldown)
        if not (go_long or go_short):
            continue

        side = "buy" if go_long else "sell"
        entry = mark * (1 - entry_off if side == "buy" else 1 + entry_off)
        # ATR stop
        atr_k = float(cfg.get("atr_k_stop", 1.8) or 1.8)
        stop = (entry - atr_k * atr) if side == "buy" else (entry + atr_k * atr)

        cc = ex.norm_ccxt_symbol(symbol)
        meta = MarketMeta(ex.client.markets.get(cc, {}))
        entry = quantize_price(entry, meta)
        stop = quantize_price(stop, meta)

        rp = _risk_params(user_id)
        pulse_factor = (decision_sig.components.get("telegram_pulse", {}) or {}).get("factor", 1.0)
        sizing = size_with_pulse(symbol, side, entry, stop, atr, pulse_factor, rp, meta, mark_price=mark)
        qty = sizing.get("qty", 0.0)
        if qty <= 0:
            continue

        try:
            # place entry post-only ve OCO kolları
            order = ex.client.create_order(cc, "limit", side, qty, entry, {"timeInForce": "PO"})
            rr = 1.2
            if side == "buy":
                tp = quantize_price(entry + rr * (entry - stop), meta)
                sl = stop
            else:
                tp = quantize_price(entry - rr * (stop - entry), meta)
                sl = stop
            ex.place_oco(cc, side, qty, entry, tp, sl)
            _last_trade_at[symbol + (":LONG" if side == "buy" else ":SHORT")] = _now_utc()
            log_event("STRAT_OPEN", {"symbol": symbol, "side": side, "entry": entry, "tp": tp, "sl": sl, "qty": qty, "pulse": pulse_factor})
        except Exception as e:
            log_event("ERROR", {"scope": "perp_breakout", "symbol": symbol, "err": str(e)})




# --- Minimal API Registry (stub) for perp_breakout_api ---
from dataclasses import dataclass
import threading
import uuid


@dataclass
class BreakoutParams:
    symbol: str = "BTCUSDT"
    exchange: str = "binance"
    testnet: bool = True
    dry_run: bool = True
    bar: str = "5m"
    lookback: int = 60
    vol_ma_period: int = 20
    max_leverage: int = 3
    sl_pct: float = 0.015
    tp_pct: float = 0.03
    notional_usd: float = 50.0


class _BreakoutTask:
    def __init__(self, task_id: str, params: BreakoutParams) -> None:
        self.id = task_id
        self.params = params
        self.stopped = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _loop() -> None:
            log_event("BREAKOUT_START", {"task_id": self.id, "params": self.params.__dict__})
            try:
                while not self.stopped:
                    try:
                        run_tick(user_id="default")
                    except Exception as e:
                        log_event("BREAKOUT_ERR", {"task_id": self.id, "error": str(e)})
                    for _ in range(60):
                        if self.stopped:
                            break
                        dt.time.sleep(1)
            finally:
                log_event("BREAKOUT_STOP", {"task_id": self.id})

        self._thread = threading.Thread(target=_loop, name=f"perp-breakout-{self.id}", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.stopped = True


class BreakoutRegistry:
    def __init__(self) -> None:
        self._tasks: Dict[str, _BreakoutTask] = {}

    def start_task(self, params: BreakoutParams) -> str:
        tid = uuid.uuid4().hex[:12]
        t = _BreakoutTask(tid, params)
        self._tasks[tid] = t
        t.start()
        return tid

    def stop_task(self, task_id: str) -> bool:
        t = self._tasks.get(task_id)
        if not t:
            return False
        t.stop()
        return True

    def status(self, task_id: Optional[str] = None) -> Dict[str, dict]:
        if task_id:
            t = self._tasks.get(task_id)
            if not t:
                return {}
            return {task_id: {"stopped": t.stopped, "params": t.params.__dict__}}
        return {k: {"stopped": v.stopped, "params": v.params.__dict__} for k, v in self._tasks.items()}


BREAKOUT_REGISTRY = BreakoutRegistry()


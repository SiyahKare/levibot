from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import duckdb as d
import pandas as pd


def ohlcv_path(symbol: str, interval: str) -> str:
    return f"backend/data/parquet/ohlcv/{symbol}_{interval}.parquet"


def eval_signals(
    day_glob: str, interval: str = "1m", horizon_min: int = 60
) -> list[dict[str, Any]]:
    sig_sql = f"""
    SELECT ts, payload->>'chat_title' AS chat, payload->'signal'->>'symbol' AS symbol,
           payload->'signal'->>'side' AS side,
           CAST(payload->'signal'->>'entry' AS DOUBLE) AS entry,
           CAST(payload->'signal'->>'sl' AS DOUBLE) AS sl,
           CAST(payload->'signal'->>'tp' AS DOUBLE) AS tp,
           payload->>'fp' AS fp
    FROM read_json_auto('{day_glob}')
    WHERE event_type='SIGNAL_EXT_TELEGRAM'
    """
    sigs = d.sql(sig_sql).df()
    if sigs.empty:
        return []

    out: list[dict[str, Any]] = []
    for _, r in sigs.iterrows():
        sym, side = r.symbol, str(r.side).upper()
        try:
            ts = dt.datetime.fromisoformat(str(r.ts).replace("Z", "+00:00"))
        except Exception:
            continue
        path = ohlcv_path(sym, interval)
        if not Path(path).exists():
            continue
        end_ts = ts + dt.timedelta(minutes=int(horizon_min))
        ohlcv = d.sql(
            f"""
            SELECT time, open, high, low, close FROM read_parquet('{path}')
            WHERE time BETWEEN TIMESTAMP '{ts:%Y-%m-%d %H:%M:%S}' AND TIMESTAMP '{end_ts:%Y-%m-%d %H:%M:%S}'
            ORDER BY time
            """
        ).df()
        if ohlcv.empty:
            continue
        entry_px = (
            float(r.entry)
            if pd.notna(r.entry) and r.entry
            else float(ohlcv.iloc[0].open)
        )
        tp_px = (
            float(r.tp)
            if pd.notna(r.tp) and r.tp
            else (entry_px * (1 + (0.01 if side == "LONG" else -0.01)))
        )
        sl_px = (
            float(r.sl)
            if pd.notna(r.sl) and r.sl
            else (entry_px * (1 - (0.008 if side == "LONG" else -0.008)))
        )

        hit_tp = False
        hit_sl = False
        mfe = 0.0
        mae = 0.0
        for _, b in ohlcv.iterrows():
            high = float(b.high)
            low = float(b.low)
            pnl_now = high - entry_px if side == "LONG" else entry_px - low
            mfe = max(mfe, pnl_now)
            mae = min(mae, (low - entry_px if side == "LONG" else entry_px - high))
            if side == "LONG":
                if high >= tp_px:
                    hit_tp = True
                    break
                if low <= sl_px:
                    hit_sl = True
                    break
            else:
                if low <= tp_px:
                    hit_tp = True
                    break
                if high >= sl_px:
                    hit_sl = True
                    break

        outcome = "TP" if hit_tp else ("SL" if hit_sl else "HORIZON")
        rr = (
            (tp_px - entry_px) / abs(entry_px - sl_px)
            if side == "LONG"
            else (entry_px - tp_px) / abs(sl_px - entry_px)
        )
        out.append(
            {
                "ts": str(r.ts),
                "chat": r.chat,
                "symbol": sym,
                "side": side,
                "entry": entry_px,
                "tp": tp_px,
                "sl": sl_px,
                "outcome": outcome,
                "rr": float(rr),
                "mfe": float(mfe),
                "mae": float(mae),
                "fp": r.fp,
            }
        )
    return out


def save_eval_parquet(
    rows: list[dict[str, Any]],
    out_path: str = "backend/data/derived/telegram_eval.parquet",
) -> str:
    if not rows:
        return out_path
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(p)
    return str(p)

from __future__ import annotations

from fastapi import APIRouter, Query
from ..infra import duck as duckinfra
import glob
import duckdb
from ..reports.telegram_reputation import compute_reputation


router = APIRouter()


@router.get("/telegram/signals")
def telegram_signals(limit: int = Query(50, le=500)):
    # Günlük log dosyaları ve geçmiş günler için glob kullan
    pattern = str(duckinfra.Path(__file__).resolve().parents[3] / "backend" / "data" / "logs" / "*" / "events-*.jsonl")
    files = sorted(glob.glob(pattern))
    if not files:
        return []
    con = duckdb.connect()
    rel = con.sql(
        f"""
        SELECT ts,
               payload->>'chat_title' AS chat_title,
               payload->'signal'->>'symbol' AS symbol,
               payload->'signal'->>'side' AS side,
               TRY_CAST(payload->'signal'->>'confidence' AS DOUBLE) AS confidence,
               COALESCE(payload->>'fp', trace_id) AS trace_id
        FROM read_json_auto('{pattern}')
        WHERE event_type = 'SIGNAL_EXT_TELEGRAM'
        ORDER BY ts DESC
        LIMIT {int(limit)}
        """
    )
    rows = rel.fetchall()
    cols = ["ts", "chat_title", "symbol", "side", "confidence", "trace_id"]
    return [dict(zip(cols, r)) for r in rows]


@router.get("/telegram/reputation")
def telegram_reputation(days: int = 14):
    pattern = str(duckinfra.Path(__file__).resolve().parents[3] / "backend" / "data" / "logs" / "*" / "events-*.jsonl")
    rep = compute_reputation(pattern, eval_parquet="backend/data/derived/telegram_eval.parquet", days=days)
    return {"window_days": days, "groups": rep}



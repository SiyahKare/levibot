from __future__ import annotations

import glob
from typing import Any

import duckdb
from fastapi import APIRouter, HTTPException, Query

from ..ai.openai_client import telegram_ai_answer
from ..infra import duck as duckinfra
from ..reports.telegram_reputation import compute_reputation

router = APIRouter()


@router.get("/telegram/signals")
def telegram_signals(limit: int = Query(50, le=500)):
    # Günlük log dosyaları ve geçmiş günler için glob kullan
    pattern = str(
        duckinfra.Path(__file__).resolve().parents[3]
        / "backend"
        / "data"
        / "logs"
        / "*"
        / "events-*.jsonl"
    )
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
    pattern = str(
        duckinfra.Path(__file__).resolve().parents[3]
        / "backend"
        / "data"
        / "logs"
        / "*"
        / "events-*.jsonl"
    )
    rep = compute_reputation(
        pattern, eval_parquet="backend/data/derived/telegram_eval.parquet", days=days
    )
    return {"window_days": days, "groups": rep}


@router.post("/telegram/ai/brain/ask")
def telegram_ai_brain_ask(payload: dict[str, Any]):
    question = str(payload.get("question", "")).strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    signals = payload.get("signals")
    if signals is not None and not isinstance(signals, list):
        raise HTTPException(status_code=400, detail="signals must be a list")

    metrics = payload.get("metrics")
    if metrics is not None and not isinstance(metrics, dict):
        raise HTTPException(status_code=400, detail="metrics must be an object")

    try:
        answer = telegram_ai_answer(question, signals=signals, metrics=metrics)
        return {"ok": True, **answer}
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/telegram/status")
def telegram_status():
    """Get Telegram bot status and configuration (safe for client)."""
    import os

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    alert_chat_id = os.getenv("TELEGRAM_ALERT_CHAT_ID")

    return {
        "ok": True,
        "bot_configured": bool(bot_token),
        "alert_chat_configured": bool(alert_chat_id),
        "connection": "active" if bot_token else "not_configured",
    }


@router.post("/telegram/test-alert")
def telegram_test_alert(payload: dict[str, Any]):
    """Send a test alert to Telegram."""
    message = str(payload.get("message", "")).strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    try:
        from ..alerts.notify import send as send_telegram

        send_telegram(message)
        return {"ok": True, "message": "Test alert sent"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send test alert: {str(e)}"
        )

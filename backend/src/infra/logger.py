from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

SENSITIVE_KEYS = {"api_key", "secret", "token", "password", "access_token", "refresh_token", "authorization"}


def _inc_event_metric(event_type: str) -> None:
    """Increment event counter; safe import to avoid circular dependency."""
    try:
        from .metrics import inc_event
        inc_event(event_type)
    except Exception:
        pass


def _mask_value(v: Any) -> Any:
    if not isinstance(v, str):
        return v
    if len(v) <= 6:
        return "***"
    return v[:2] + "***" + v[-2:]


def _mask_payload(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: Dict[str, Any] = {}
        for k, v in obj.items():
            if k.lower() in SENSITIVE_KEYS:
                out[k] = _mask_value(v)
            else:
                out[k] = _mask_payload(v)
        return out
    if isinstance(obj, list):
        return [_mask_payload(x) for x in obj]
    return obj


def _logs_dir_for_now() -> Path:
    base = Path(__file__).resolve().parents[3] / "backend" / "data" / "logs"
    day = datetime.utcnow().strftime("%Y-%m-%d")
    d = base / day
    d.mkdir(parents=True, exist_ok=True)
    return d


def log_event(event_type: str, payload: Dict[str, Any], symbol: Optional[str] = None, trace_id: Optional[str] = None) -> None:
    ts = datetime.utcnow().isoformat() + "Z"
    rec = {
        "ts": ts,
        "event_type": event_type,
        "symbol": symbol,
        "payload": _mask_payload(payload),
        "trace_id": trace_id or os.getenv("TRACE_ID"),
    }
    day_dir = _logs_dir_for_now()
    # shard by hour for simpler file sizes
    hour = datetime.utcnow().strftime("%H")
    fp = day_dir / f"events-{hour}.jsonl"
    with open(fp, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    # Increment event counter metric
    _inc_event_metric(event_type)
    
    # PR-42: Publish to WebSocket EventBus (non-blocking)
    try:
        import asyncio
        from backend.src.infra.ws_bus import BUS
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(BUS.publish(rec))
        else:
            # If no event loop is running, skip publishing
            pass
    except Exception:
        # Silently fail if EventBus is not available
        pass


class JsonlEventLogger:
    def __init__(self, default_symbol: Optional[str] = None, default_trace_id: Optional[str] = None) -> None:
        self.default_symbol = default_symbol
        self.default_trace_id = default_trace_id

    def write(self, event_type: str, payload: Dict[str, Any], symbol: Optional[str] = None, trace_id: Optional[str] = None) -> None:
        log_event(
            event_type,
            payload,
            symbol=symbol or self.default_symbol,
            trace_id=trace_id or self.default_trace_id,
        )


__all__ = ["log_event", "JsonlEventLogger"]

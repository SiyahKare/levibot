from __future__ import annotations

from fastapi.testclient import TestClient
from backend.src.app.main import app
from datetime import datetime
from pathlib import Path
import glob
import json


def test_paper_order_creates_events():
    trace = f"test-{datetime.utcnow().timestamp()}"
    c = TestClient(app)
    r = c.post(
        "/paper/order",
        params={
            "symbol": "ETHUSDT",
            "side": "buy",
            "notional_usd": 10,
            "trace_id": trace,
        },
    )
    assert r.status_code == 200 and r.json().get("ok") is True

    day = datetime.utcnow().strftime("%Y-%m-%d")
    base = Path(__file__).resolve().parents[2] / "backend" / "data" / "logs" / day
    files = sorted(glob.glob(str(base / "events-*.jsonl")))
    assert files, "no log files created"
    seen = set()
    trace_ids = set()
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("trace_id") == trace:
                    trace_ids.add(rec.get("trace_id"))
                    et = rec.get("event_type")
                    if et:
                        seen.add(et)
    assert {"ORDER_NEW", "ORDER_FILLED", "POSITION_CLOSED"} <= seen
    # Aynı trace_id ile üç event de gelmiş olmalı
    assert trace in trace_ids



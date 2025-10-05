from __future__ import annotations

from fastapi.testclient import TestClient
from backend.src.app.main import app
from datetime import datetime
from pathlib import Path
import glob
import json


def test_cex_paper_order_creates_events():
    c = TestClient(app)
    trace = f"test-{datetime.utcnow().timestamp()}"
    r = c.post(
        "/exec/cex/paper-order",
        params={
            "exchange": "binance",
            "symbol": "ETH/USDT",
            "side": "buy",
            "notional_usd": 5,
            "trace_id": trace,
        },
    )
    assert r.status_code == 200 and r.json().get("ok") is True

    # JSONL taraması (son gün)
    day = datetime.utcnow().strftime("%Y-%m-%d")
    base = Path(__file__).resolve().parents[2] / "backend" / "data" / "logs" / day
    files = sorted(glob.glob(str(base / "events-*.jsonl")))
    assert files, "no log files created"

    seen = set()
    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("trace_id") == trace and rec.get("event_type"):
                    seen.add(rec["event_type"])
    assert {"ORDER_NEW", "ORDER_PARTIAL_FILL", "ORDER_FILLED", "POSITION_CLOSED"} <= seen




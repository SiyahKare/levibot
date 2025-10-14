from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.src.app.main import app


def test_cex_paper_order_creates_events(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    data_dir = tmp_path / "data"
    log_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("SECURITY_ENABLED", "false")

    c = TestClient(app)
    trace = f"test-{datetime.now(UTC).timestamp()}"
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

    day = datetime.now(UTC).strftime("%Y-%m-%d")
    base = log_dir / day
    files = sorted(base.glob("events-*.jsonl"))
    assert files, "no log files created"

    seen = set()
    for fp in files:
        with fp.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("trace_id") == trace and rec.get("event_type"):
                    seen.add(rec["event_type"])
    assert {
        "ORDER_NEW",
        "ORDER_PARTIAL_FILL",
        "ORDER_FILLED",
        "POSITION_CLOSED",
    } <= seen

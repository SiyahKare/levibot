from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from backend.src.app.main import app


def _event_files(base: Path) -> list[Path]:
    return sorted(base.glob("events-*.jsonl"))


def _events_for_trace(files: list[Path], trace_id: str) -> set[str]:
    seen: set[str] = set()
    for fp in files:
        with fp.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("trace_id") == trace_id and rec.get("event_type"):
                    seen.add(rec["event_type"])
    return seen


def test_paper_order_creates_events(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LOG_DIR", str(log_dir))
    monkeypatch.setenv("SECURITY_ENABLED", "false")

    trace = f"test-{datetime.now(UTC).timestamp()}"
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

    day = datetime.now(UTC).strftime("%Y-%m-%d")
    base = log_dir / day
    files = _event_files(base)
    assert files, "no log files created"
    seen = _events_for_trace(files, trace)
    assert {"ORDER_NEW", "ORDER_FILLED", "POSITION_CLOSED"} <= seen



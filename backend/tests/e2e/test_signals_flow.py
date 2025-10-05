from __future__ import annotations
import httpx, json, glob
from datetime import datetime
import pytest

def _today_log_glob():
    day = datetime.utcnow().strftime("%Y-%m-%d")
    return sorted(glob.glob(f"backend/data/logs/{day}/events-*.jsonl"))

def _grep(log_files, needle):
    for fp in log_files:
        with open(fp, "r", encoding="utf-8") as f:
            for line in f:
                if needle in line:
                    return True
    return False

@pytest.mark.e2e
def test_health_and_score(base_url):
    with httpx.Client(base_url=base_url, headers={"X-API-Key":"test-e2e"}, timeout=5.0) as c:
        r = c.get("/healthz"); assert r.status_code == 200 and r.json().get("ok") is True
        r = c.post("/signals/score", params={"text":"BUY BTCUSDT @ 60000"})
        assert r.status_code == 200
        j = r.json()
        assert j["label"] in ("BUY","SELL","NO-TRADE")
        assert 0.0 <= float(j["confidence"]) <= 1.0

@pytest.mark.e2e
def test_ingest_and_events(base_url):
    txt = "BUY BTCUSDT @ 60000 tp 62000 sl 58500"
    with httpx.Client(base_url=base_url, headers={"X-API-Key":"test-e2e"}, timeout=5.0) as c:
        r = c.post("/signals/ingest-and-score", params={"text":txt,"source":"e2e","channel":"@test"})
        assert r.status_code == 200
        j = r.json(); assert j.get("ok") is True
    files = _today_log_glob()
    assert files, "no log files created"
    assert _grep(files, "SIGNAL_INGEST")
    assert _grep(files, "SIGNAL_SCORED")
    # autoroute dry-run event (guard açık olabilir)
    assert _grep(files, "AUTO_ROUTE_DRYRUN") or _grep(files, "AUTO_ROUTE_SKIPPED")

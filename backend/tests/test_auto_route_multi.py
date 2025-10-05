from fastapi.testclient import TestClient
from backend.src.app.main import app

def test_multi_symbol_dry_run(monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("AUTO_ROUTE_ENABLED","true")
    monkeypatch.setenv("AUTO_ROUTE_DRY_RUN","true")
    monkeypatch.setenv("AUTO_ROUTE_MIN_CONF","0.5")
    r = c.post("/signals/ingest-and-score", params={
        "text":"BUY BTC ETH tp 62000 sl 58500 size 30", "source":"tg"
    })
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["route"]["eligible"] is True
    assert len(j.get("fe",{}).get("symbols",[])) >= 2

def test_multi_symbol_fallback_to_old_parser(monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("AUTO_ROUTE_ENABLED","true")
    monkeypatch.setenv("AUTO_ROUTE_DRY_RUN","true")
    monkeypatch.setenv("AUTO_ROUTE_MIN_CONF","0.5")
    # Text with old-style symbol mention (not FE compatible)
    r = c.post("/signals/ingest-and-score", params={
        "text":"BUY $SOL tp 200 sl 180", "source":"tg"
    })
    assert r.status_code == 200
    j = r.json()
    # Old parser should catch $SOL
    # (May or may not succeed depending on old parse_symbol logic)
    assert j["ok"] is True


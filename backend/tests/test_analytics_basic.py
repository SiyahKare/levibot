from fastapi.testclient import TestClient

from backend.src.app.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_stats_ok():
    r = client.get("/analytics/stats?days=1")
    assert r.status_code == 200
    body = r.json()
    assert "total" in body and "event_types" in body


def test_timeseries_ok():
    r = client.get("/analytics/timeseries?interval=5m&days=1")
    assert r.status_code == 200
    assert "points" in r.json()


def test_traces_ok():
    r = client.get("/analytics/traces?days=1&limit=10")
    assert r.status_code == 200
    assert "rows" in r.json()

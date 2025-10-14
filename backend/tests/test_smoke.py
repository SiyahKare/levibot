from __future__ import annotations

from fastapi.testclient import TestClient

from backend.src.app.main import app


def test_status_endpoint():
    client = TestClient(app)
    r = client.get("/status")
    assert r.status_code == 200
    data = r.json()
    assert "running" in data


def test_events_smoke():
    client = TestClient(app)
    r = client.get("/events", params={"limit": 3})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

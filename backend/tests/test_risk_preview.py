from __future__ import annotations

from fastapi.testclient import TestClient

from backend.src.app.main import app


def test_risk_preview_endpoint():
    c = TestClient(app)
    r = c.post("/risk/preview", params={"side": "buy", "price": 100})
    assert r.status_code == 200
    j = r.json()
    assert "sl" in j and "tp" in j and j["sl"] < 100 < j["tp"]

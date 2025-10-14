from __future__ import annotations

from fastapi.testclient import TestClient

from backend.src.app.main import app


def test_livez_readyz_smoke():
    c = TestClient(app)
    r1 = c.get("/livez")
    assert r1.status_code == 200 and r1.json().get("ok") is True
    r2 = c.get("/readyz")
    assert r2.status_code == 200 and "ok" in r2.json()

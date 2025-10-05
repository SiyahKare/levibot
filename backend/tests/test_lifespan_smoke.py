from __future__ import annotations
from fastapi.testclient import TestClient
from backend.src.app.main import app


def test_lifespan_healthz():
    """Smoke test: lifespan handler doesn't break healthz."""
    with TestClient(app) as c:
        r = c.get("/healthz")
        assert r.status_code == 200
        assert r.json().get("ok") is True


def test_lifespan_metrics():
    """Smoke test: build_info metric is set on startup."""
    with TestClient(app) as c:
        r = c.get("/metrics/prom")
        assert r.status_code == 200
        # Check that build_info metric exists (may be "dev" or actual version)
        assert b"levibot_build_info" in r.content

from fastapi.testclient import TestClient

from apps.executor.main import create_app


def test_readyz_mock():
    """Test readyz endpoint in mock mode (no RPC)"""
    c = TestClient(create_app())
    r = c.get("/readyz")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "ready" in data
    assert "mode" in data


def test_readyz_with_rpc():
    """Test readyz endpoint with RPC (if available)"""
    import os

    if not os.getenv("RPC_BASE_SEPOLIA"):
        # Skip if no RPC configured
        return

    c = TestClient(create_app())
    r = c.get("/readyz")
    assert r.status_code in (200, 503)
    data = r.json()
    assert "ready" in data
    if r.status_code == 200:
        assert data["mode"] == "real"
        assert "block" in data
    else:
        assert data["mode"] == "mock"

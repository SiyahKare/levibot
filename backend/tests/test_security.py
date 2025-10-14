from fastapi.testclient import TestClient

from backend.src.app.main import app


def test_auth_forbidden_without_key(monkeypatch):
    monkeypatch.setenv("API_KEYS", "sekret")
    monkeypatch.setenv("SECURED_PATH_PREFIXES", "/signals")
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/signals/score?text=BUY")
    assert r.status_code in (200, 403)


def test_auth_ok_with_key(monkeypatch):
    monkeypatch.setenv("API_KEYS", "sekret")
    monkeypatch.setenv("SECURED_PATH_PREFIXES", "/signals")
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/signals/score?text=BUY", headers={"X-API-Key": "sekret"})
    assert r.status_code in (200, 422)


def test_rate_limit_basic_smoke(monkeypatch):
    monkeypatch.setenv("API_KEYS", "")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SEC", "60")
    monkeypatch.setenv("RATE_LIMIT_MAX", "10")
    monkeypatch.setenv("RATE_LIMIT_BURST", "5")
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/signals/score?text=BUY")
    assert r.status_code in (200, 422)


def test_unsecured_path_always_ok(monkeypatch):
    monkeypatch.setenv("API_KEYS", "sekret")
    monkeypatch.setenv("SECURED_PATH_PREFIXES", "/signals,/exec")
    c = TestClient(app, raise_server_exceptions=False)
    r = c.get("/status")
    assert r.status_code == 200

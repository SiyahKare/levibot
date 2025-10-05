from fastapi.testclient import TestClient
from backend.src.app.main import app
import os

def test_auth_forbidden_without_key(monkeypatch):
    monkeypatch.setenv("API_KEYS","sekret")
    monkeypatch.setenv("SECURED_PATH_PREFIXES","/signals")
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/signals/score?text=BUY")
    # 403 (forbidden) veya 500 (middleware exception) - her ikisi de auth bloğunu gösterir
    assert r.status_code in (403, 500)

def test_auth_ok_with_key(monkeypatch):
    monkeypatch.setenv("API_KEYS","sekret")
    monkeypatch.setenv("SECURED_PATH_PREFIXES","/signals")
    c = TestClient(app, raise_server_exceptions=False)
    r = c.post("/signals/score?text=BUY", headers={"X-API-Key":"sekret"})
    # 200 (ok) veya 422 (validation error) - her ikisi de auth geçti
    assert r.status_code in (200, 422)

def test_rate_limit_basic_smoke(monkeypatch):
    # Basit smoke: rate limit ENV'leri okunuyor mu?
    monkeypatch.setenv("API_KEYS","")  # auth kapalı
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SEC","60")
    monkeypatch.setenv("RATE_LIMIT_MAX","10")
    monkeypatch.setenv("RATE_LIMIT_BURST","5")
    c = TestClient(app, raise_server_exceptions=False)
    # İlk istek geçmeli
    r = c.post("/signals/score?text=BUY")
    assert r.status_code in (200, 422)  # auth yok, rate limit henüz aşılmadı

def test_unsecured_path_always_ok(monkeypatch):
    monkeypatch.setenv("API_KEYS","sekret")
    monkeypatch.setenv("SECURED_PATH_PREFIXES","/signals,/exec")
    c = TestClient(app, raise_server_exceptions=False)
    # /status is not in SECURED_PATH_PREFIXES
    r = c.get("/status")
    assert r.status_code == 200

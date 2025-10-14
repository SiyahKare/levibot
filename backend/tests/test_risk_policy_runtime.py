from fastapi.testclient import TestClient

from backend.src.app.main import app
from backend.src.core.risk import _reset as reset_risk_policy_state


def test_get_and_put_policy(monkeypatch):
    reset_risk_policy_state()
    c = TestClient(app)
    r1 = c.get("/risk/policy")
    assert r1.status_code == 200
    cur = r1.json().get("current")
    assert cur in ("conservative","moderate","aggressive")

    r2 = c.put("/risk/policy", json={"name":"aggressive"})
    assert r2.status_code == 200
    assert r2.json().get("current") == "aggressive"

    r3 = c.get("/risk/policy")
    assert r3.status_code == 200
    assert r3.json().get("current") == "aggressive"

def test_put_invalid_policy():
    c = TestClient(app)
    r = c.put("/risk/policy", json={"name":"yolo"})
    assert r.status_code == 400

def test_policy_response_structure():
    c = TestClient(app)
    r = c.get("/risk/policy")
    assert r.status_code == 200
    j = r.json()
    assert "current" in j
    assert "choices" in j
    assert "multipliers" in j
    assert "cooldown_sec" in j
    assert isinstance(j["choices"], list)

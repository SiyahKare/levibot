from fastapi.testclient import TestClient

from apps.executor.main import create_app


def test_miniface():
    c = TestClient(create_app())
    assert c.get("/healthz").status_code == 200
    r = c.post(
        "/signals/run",
        json={"strategy": "sma", "params": {"fast": 10, "slow": 50}, "fee_bps": 10},
    )
    assert r.status_code == 200
    js = r.json()
    assert "metrics" in js and "orders" in js
    r2 = c.post("/exec/dry-run", json={"orders": js["orders"], "slippage_bps": 25})
    assert r2.status_code == 200
    js2 = r2.json()
    assert "fills" in js2 and "pnl" in js2

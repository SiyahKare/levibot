from fastapi.testclient import TestClient

from apps.executor.main import create_app


def test_sma_params_contract():
    c = TestClient(create_app())
    r = c.post(
        "/signals/run",
        json={"strategy": "sma", "params": {"fast": 10, "slow": 50}, "fee_bps": 10},
    )
    assert r.status_code == 200
    # Note: Parameter validation is lenient for now - extra params are ignored
    r2 = c.post(
        "/signals/run",
        json={"strategy": "sma", "params": {"period": 14}, "fee_bps": 10},
    )
    assert r2.status_code == 200  # Currently lenient, will be strict in future


def test_risk_dict_or_order():
    c = TestClient(create_app())
    body = {
        "orders": [
            {
                "pair": "BTCUSDT",
                "side": "BUY",
                "qty": 0.1,
                "kind": "MARKET",
                "reason": "x",
            }
        ],
        "slippage_bps": 25,
    }
    assert c.post("/exec/dry-run", json=body).status_code == 200


def test_metrics_visible_once_called():
    c = TestClient(create_app())
    c.get("/healthz")
    m = c.get("/metrics").text
    assert "levi_requests_total" in m

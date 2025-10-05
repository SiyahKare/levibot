from fastapi.testclient import TestClient
from backend.src.app.main import app


def test_signal_score_endpoints():
    c = TestClient(app)
    r = c.post("/signals/score", params={"text": "BUY BTCUSDT @ 60000"})
    assert r.status_code == 200
    j = r.json()
    assert j["label"] in {"BUY", "SELL", "NO-TRADE"}
    assert 0 <= j["confidence"] <= 1

    r2 = c.post("/signals/ingest-and-score", params={"text": "avoid news, no trade", "source": "tg"})
    assert r2.status_code == 200
    j2 = r2.json()
    assert j2["label"] in {"BUY", "SELL", "NO-TRADE"}




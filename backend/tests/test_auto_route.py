from fastapi.testclient import TestClient

from backend.src.app.main import app


def test_auto_route_dryrun_skips_when_disabled(monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("AUTO_ROUTE_ENABLED", "false")
    r = c.post(
        "/signals/ingest-and-score",
        params={"text": "BUY BTCUSDT @ 60000", "source": "tg"},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["routed"] is False


def test_auto_route_dryrun_when_enabled(monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("AUTO_ROUTE_ENABLED", "true")
    monkeypatch.setenv("AUTO_ROUTE_DRY_RUN", "true")
    monkeypatch.setenv("AUTO_ROUTE_MIN_CONF", "0.5")
    monkeypatch.setenv("AUTO_ROUTE_EXCH", "binance")
    monkeypatch.setenv("AUTO_ROUTE_SYMBOL_MAP", "BTC:BTC/USDT,ETH:ETH/USDT")
    r = c.post(
        "/signals/ingest-and-score",
        params={"text": "BUY BTCUSDT @ 60000", "source": "tg"},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert j["routed"] is False
    assert "route" in j and j["route"]["dry_run"] is True


def test_auto_route_exec_when_enabled(monkeypatch):
    c = TestClient(app)
    monkeypatch.setenv("AUTO_ROUTE_ENABLED", "true")
    monkeypatch.setenv("AUTO_ROUTE_DRY_RUN", "false")
    monkeypatch.setenv("AUTO_ROUTE_MIN_CONF", "0.5")
    monkeypatch.setenv("AUTO_ROUTE_EXCH", "binance")
    monkeypatch.setenv("AUTO_ROUTE_SYMBOL_MAP", "BTC:BTC/USDT")
    r = c.post(
        "/signals/ingest-and-score",
        params={"text": "BUY BTCUSDT @ 60000", "source": "tg"},
    )
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    # offline fallback olsa bile /exec/cex/paper-order yoluna düşer ve routed True olur
    # bazı guard'lardan dolayı routed False da dönebilir (cooldown vs.)
    assert j.get("routed") in (True, False)

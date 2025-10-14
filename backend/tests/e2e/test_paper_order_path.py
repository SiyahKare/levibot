from __future__ import annotations

import httpx
import pytest


@pytest.mark.e2e
def test_cex_paper_order_offline(base_url):
    with httpx.Client(
        base_url=base_url, headers={"X-API-Key": "test-e2e"}, timeout=5.0
    ) as c:
        r = c.post(
            "/exec/cex/paper-order",
            params={
                "exchange": "binance",
                "symbol": "ETH/USDT",
                "side": "buy",
                "notional_usd": 5,
            },
        )
        assert r.status_code == 200
        j = r.json()
        assert j["ok"] is True and j["symbol"] == "ETH/USDT" and j["qty"] > 0

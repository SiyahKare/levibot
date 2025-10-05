from __future__ import annotations

from backend.src.core.risk import RiskEngine, RiskConfig


def test_cooldown_blocks_second_order():
    r = RiskEngine(RiskConfig(cooldown_sec=5))
    ok1, reason1 = r.allow("ETHUSDT", 10)
    assert ok1 and reason1 == "ok"
    r.record("ETHUSDT")
    ok2, reason2 = r.allow("ETHUSDT", 10)
    assert (not ok2) and reason2 == "risk/cooldown"


def test_sl_tp_fallback_and_sign():
    r = RiskEngine(RiskConfig(fallback_sl_pct=0.01, fallback_tp_pct=0.02))
    sl_buy, tp_buy = r.sl_tp("buy", 100.0, atr=None)
    assert sl_buy < 100 and tp_buy > 100
    sl_sell, tp_sell = r.sl_tp("sell", 100.0, atr=None)
    assert sl_sell > 100 and tp_sell < 100




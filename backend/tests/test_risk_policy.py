
from backend.src.core.risk import _reset, current_policy, derive_sl_tp


def test_policy_names(monkeypatch):
    monkeypatch.setenv("RISK_POLICY","aggressive")
    _reset()
    assert current_policy().name == "aggressive"
    monkeypatch.setenv("RISK_POLICY","conservative")
    _reset()
    assert current_policy().name == "conservative"

def test_derive_from_atr_buy():
    sl, tp, meta = derive_sl_tp("buy", price=100, atr=5, tp_hint=None, sl_hint=None)
    assert sl < 100 and tp > 100
    assert meta["source"] == "atr"

def test_hint_has_priority():
    sl, tp, meta = derive_sl_tp("sell", price=100, atr=10, tp_hint=80, sl_hint=120)
    assert sl == 120 and tp == 80 and meta["source"] == "hint"

def test_derive_from_atr_sell():
    sl, tp, meta = derive_sl_tp("sell", price=100, atr=5, tp_hint=None, sl_hint=None)
    assert sl > 100 and tp < 100
    assert meta["source"] == "atr"

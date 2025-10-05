from backend.src.core.risk import clamp_notional
import os

def test_notional_clamped(monkeypatch):
    monkeypatch.setenv("RISK_MIN_NOTIONAL","10")
    monkeypatch.setenv("RISK_MAX_NOTIONAL","50")
    assert clamp_notional(5) == 10
    assert clamp_notional(500) == 50
    assert clamp_notional(25) == 25

def test_notional_default_limits(monkeypatch):
    # Varsayılan: 5-250
    monkeypatch.delenv("RISK_MIN_NOTIONAL", raising=False)
    monkeypatch.delenv("RISK_MAX_NOTIONAL", raising=False)
    assert clamp_notional(3) == 5
    assert clamp_notional(300) == 250
    assert clamp_notional(100) == 100

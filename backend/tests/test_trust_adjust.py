from backend.src.ingest.trust import adjust_conf


def test_adjust_conf_with_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_TRUST", "@good:1.2,@meh:0.9")
    monkeypatch.setenv("TRUST_MIN", "0.5")
    monkeypatch.setenv("TRUST_MAX", "1.5")
    assert abs(adjust_conf("@good", 0.50) - 0.60) < 1e-6
    assert abs(adjust_conf("@meh", 0.80) - 0.72) < 1e-6
    assert abs(adjust_conf("@none", 0.70) - 0.70) < 1e-6



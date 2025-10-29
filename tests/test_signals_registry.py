from pkgs.signals import STRATEGIES


def test_registry_keys():
    assert {"sma", "ema", "rsi"}.issubset(set(STRATEGIES.keys()))

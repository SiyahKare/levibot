from apps.executor.risk import evaluate_and_filter
from apps.executor.schemas import Order


def test_risk_basic():
    orders = [Order(pair="BTCUSDT", side="BUY", qty=10.0, reason="t")]
    out, logs = evaluate_and_filter(orders)
    assert len(out) == 1 and not logs

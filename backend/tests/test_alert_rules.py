from backend.src.alerts.rules import load_rules, evaluate

SCORED_BUY_82 = {
    "event_type": "SIGNAL_SCORED",
    "payload": {"label":"BUY","confidence":0.82, "text":"BUY BTCUSDT @ 60000"},
}

BLOCKED_COOLDOWN = {
    "event_type": "ORDER_BLOCKED",
    "payload": {"reason":"cooldown: symbol=ETH/USDT"},
}

CLOSED_LOSS = {
    "event_type": "POSITION_CLOSED",
    "payload": {"pnl_usdt": -3.25, "qty": 0.01},
}

def test_high_conf_buy_matches(tmp_path):
    # temp alerts.yaml kullan
    p = tmp_path/"alerts.yaml"
    p.write_text("""rules:
      - id: high_conf_buy
        all:
          - { field: "event_type", op: "eq", value: "SIGNAL_SCORED" }
          - { field: "payload.label", op: "eq", value: "BUY" }
          - { field: "payload.confidence", op: "gte", value: 0.80 }
    """, encoding="utf-8")
    rules = load_rules(p)
    assert rules and rules[0].id == "high_conf_buy"
    matches = evaluate(SCORED_BUY_82, rules)
    assert [m.id for m in matches] == ["high_conf_buy"]

def test_risk_breach_any():
    # doğrudan repo'daki config'i kullanalım (PR-34 ile eklenecek)
    rules = load_rules("configs/alerts.yaml")
    ids = [r.id for r in evaluate(BLOCKED_COOLDOWN, rules)]
    assert "risk_breach" in ids

def test_negative_pnl_close():
    rules = load_rules("configs/alerts.yaml")
    ids = [r.id for r in evaluate(CLOSED_LOSS, rules)]
    assert "negative_pnl_close" in ids

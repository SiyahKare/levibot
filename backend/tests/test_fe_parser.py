from backend.src.signals.fe import parse_features

def test_parse_single_symbol_tp_sl_size():
    t = "BUY BTCUSDT @ 60000 tp 62000 sl 58500 size 25"
    fe = parse_features(t)
    assert fe["symbols"] == ["BTC/USDT"]
    assert fe["tp"] == 62000.0
    assert fe["sl"] == 58500.0
    assert fe["size"] == 25.0

def test_parse_multi_symbol_and_variants():
    t = "scalp long BTC and ETH, target 30500, s/l 29800 qty 15"
    fe = parse_features(t)
    assert "BTC/USDT" in fe["symbols"] and "ETH/USDT" in fe["symbols"]
    assert fe["tp"] == 30500.0
    assert fe["sl"] == 29800.0
    assert fe["size"] == 15.0

def test_parse_no_features():
    t = "hello world"
    fe = parse_features(t)
    assert fe["symbols"] == []
    assert fe["tp"] is None
    assert fe["sl"] is None
    assert fe["size"] is None

def test_parse_tp_sl_without_symbols():
    t = "TP at 1.2345 SL 1.0000 risk 50usd"
    fe = parse_features(t)
    assert fe["tp"] == 1.2345
    assert fe["sl"] == 1.0000
    assert fe["size"] == 50.0


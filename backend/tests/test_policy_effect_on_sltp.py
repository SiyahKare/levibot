from backend.src.core.risk import set_policy_name, derive_sl_tp

def test_policy_changes_sltp():
    # Conservative: SL=2.0×ATR, TP=1.0×ATR
    set_policy_name("conservative")
    sl1, tp1, meta1 = derive_sl_tp("buy", 100.0, 5.0, None, None)
    # Buy: SL = 100 - 2.0*5 = 90, TP = 100 + 1.0*5 = 105
    
    # Aggressive: SL=1.0×ATR, TP=2.0×ATR
    set_policy_name("aggressive")
    sl2, tp2, meta2 = derive_sl_tp("buy", 100.0, 5.0, None, None)
    # Buy: SL = 100 - 1.0*5 = 95, TP = 100 + 2.0*5 = 110
    
    # Aggressive SL daha yakın (95 > 90), TP daha uzak (110 > 105)
    assert sl2 > sl1
    assert tp2 > tp1
    assert meta1["policy"] == "conservative"
    assert meta2["policy"] == "aggressive"

def test_policy_sell_side():
    set_policy_name("moderate")
    sl, tp, meta = derive_sl_tp("sell", 100.0, 5.0, None, None)
    # Sell: SL = 100 + 1.5*5 = 107.5, TP = 100 - 1.5*5 = 92.5
    assert sl > 100
    assert tp < 100
    assert meta["policy"] == "moderate"

from backend.src.l2.yields import list_yields

def test_yields_yaml_loads():
    j = list_yields()
    assert j["ok"] is True

def test_yields_has_chains():
    j = list_yields()
    assert "chains" in j
    assert isinstance(j["chains"], list)

def test_yields_arbitrum_exists():
    j = list_yields()
    chains = j.get("chains", [])
    arb = next((c for c in chains if c.get("name") == "arbitrum"), None)
    assert arb is not None
    assert len(arb.get("protocols", [])) > 0

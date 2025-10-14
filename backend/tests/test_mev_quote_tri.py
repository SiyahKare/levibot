import asyncio

from backend.src.mev.quote import quote_symbol, tri_opportunity


def test_quote_offline_fallback_ok():
    j = asyncio.run(quote_symbol("ethereum", "ETH", "USDC", 0.1))
    assert j["ok"] is True and "price" in j


def test_quote_unsupported_token():
    j = asyncio.run(quote_symbol("ethereum", "UNKNOWN", "USDC", 0.1))
    assert j["ok"] is False


def test_tri_math():
    assert abs(tri_opportunity(1.01, 1.01, 0.99) - (1.01 * 1.01 * 0.99 - 1.0)) < 1e-9


def test_tri_positive_edge():
    # 1.02 * 1.02 * 0.97 = 1.0096 → edge = 0.0096
    edge = tri_opportunity(1.02, 1.02, 0.97)
    assert edge > 0.0


def test_tri_negative_edge():
    # 0.99 * 0.99 * 0.99 = 0.970299 → edge = -0.029701
    edge = tri_opportunity(0.99, 0.99, 0.99)
    assert edge < 0.0

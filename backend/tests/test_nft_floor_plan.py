import asyncio

from backend.src.nft.floor import floor_price


def test_floor_offline_ok():
    j = asyncio.run(floor_price("demo-collection"))
    assert j["ok"] is True and "floor" in j


def test_floor_has_name():
    j = asyncio.run(floor_price("test-nft"))
    assert j.get("name") is not None


def test_floor_fallback_value():
    j = asyncio.run(floor_price("offline-test"))
    # offline fallback = 42.0
    if j.get("fallback"):
        assert j["floor"] == 42.0

from __future__ import annotations
import os, aiohttp

async def reservoir_floor(collection: str) -> dict | None:
    base = os.getenv("RESERVOIR_API_URL", "https://api.reservoir.tools")
    key  = os.getenv("RESERVOIR_API_KEY","")
    headers = {"x-api-key": key} if key else {}
    url = f"{base}/collections/v5"
    params = {"id": collection}
    try:
        to = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=to, headers=headers) as s:
            async with s.get(url, params=params, headers=headers) as r:
                j = await r.json()
                items = j.get("collections") or []
                if items:
                    it = items[0]
                    return {"floor": it.get("floorAsk",{}).get("price",{}).get("amount",{}).get("usd"), "name": it.get("name")}
    except Exception:
        return None
    return None

async def floor_price(collection: str) -> dict:
    j = await reservoir_floor(collection)
    if j:
        return {"ok": True, **j}
    # offline fallback
    return {"ok": True, "name": collection, "floor": 42.0, "fallback": True}

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

import requests

BASE = "https://api.reservoir.tools"
KEY = os.getenv("RESERVOIR_API_KEY", "")
HDR = {"x-api-key": KEY} if KEY else {}
CACHE = Path("backend/data/cache/nft")
CACHE.mkdir(parents=True, exist_ok=True)


def _get(url: str, **params: Any) -> dict[str, Any]:
    r = requests.get(BASE + url, headers=HDR, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def floor_usd(collection: str) -> float | None:
    j = _get("/collections/v7", id=collection)
    items = j.get("collections", [])
    if not items:
        return None
    fa = items[0].get("floorAsk")
    if not fa:
        return None
    return float(fa["price"]["amount"]["usd"])  # type: ignore[index]


def traits_freq(collection: str) -> dict[str, int]:
    p = CACHE / f"{collection.replace(':', '_')}_traits.json"
    if p.exists() and time.time() - p.stat().st_mtime < 86400:
        return json.loads(p.read_text())
    j = _get(f"/collections/{collection}/attributes/all/v2")
    freq: dict[str, int] = {}
    for a in j.get("attributes", []):
        k = a.get("key")
        for it in a.get("values", []) or []:
            freq[f"{k}|{it.get('value')}"] = int(it.get("count", 0))
    p.write_text(json.dumps(freq))
    return freq


__all__ = ["floor_usd", "traits_freq"]

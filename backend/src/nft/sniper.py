from __future__ import annotations

import os
from typing import Any

import requests

from ..infra.logger import log_event
from .traits import floor_usd as fetch_floor_usd
from .traits import traits_freq

BASE = "https://api.reservoir.tools"
APIKEY = os.getenv("RESERVOIR_API_KEY", "")


def fetch_listings(collection: str, limit: int = 50) -> list[dict[str, Any]]:
    r = requests.get(
        f"{BASE}/orders/asks/v5",
        headers={"x-api-key": APIKEY} if APIKEY else {},
        params={"collection": collection, "limit": limit, "status": "active"},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("orders", [])


def scan_collection(collection: str, floor_min_usd: float, rare_min: float) -> None:
    floor = fetch_floor_usd(collection) or 0.0
    freq = traits_freq(collection)
    orders = fetch_listings(collection)
    if not orders:
        return
    for o in orders:
        try:
            ask = float(o["price"]["amount"]["usd"])
            # kaba rarity: ilk birkaç trait frekansının tersine orantılı skor
            traits = (
                o.get("criteria", {}).get("data", {}).get("token", {}).get("attributes")
                or []
            )
            if traits:
                inv = 0.0
                for t in traits[:5]:
                    key = f"{t.get('key')}|{t.get('value')}"
                    inv += 1.0 / float(freq.get(key, 1) or 1)
                rare_score = min(1.0, inv / 50.0)
            else:
                rare_score = 0.5
            spread = (ask - floor) / max(floor, 1e-9) * 100.0
            if ask <= floor_min_usd and rare_score >= rare_min and spread <= 2.0:
                log_event(
                    "NFT_SNIPE_CANDIDATE",
                    {
                        "collection": collection,
                        "tokenId": o["criteria"]["data"]["token"]["tokenId"],
                        "ask": ask,
                        "floor": floor,
                        "rare_score": rare_score,
                        "spread_pct": spread,
                        "provider": "reservoir",
                        "listing_id": o["id"],
                    },
                )
        except Exception:
            continue


__all__ = ["scan_collection", "fetch_listings"]

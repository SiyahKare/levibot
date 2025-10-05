from __future__ import annotations
import os, aiohttp, asyncio
from typing import Optional, Dict

TOKENS = {
    "ethereum": {
        "ETH": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    }
}

async def _http_json(url: str, headers: dict | None = None, params: dict | None = None, timeout=8) -> dict:
    to = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=to, headers=headers) as s:
        async with s.get(url, params=params) as r:
            return await r.json()

async def quote_0x(chain: str, sell: str, buy: str, sell_amount_wei: int) -> Optional[Dict]:
    base = os.getenv("ZEROX_API_URL", "https://api.0x.org/swap/v1/quote").rstrip("/")
    key  = os.getenv("ZEROX_API_KEY", "")
    headers = {"0x-api-key": key} if key else {}
    params = {"sellToken": sell, "buyToken": buy, "sellAmount": str(sell_amount_wei)}
    try:
        j = await _http_json(base, headers=headers, params=params, timeout=8)
        if "price" in j:
            return j
    except Exception:
        return None
    return None

def wei(amount: float, decimals: int = 18) -> int:
    return int(amount * (10 ** decimals))

async def quote_symbol(chain: str, sell_sym: str, buy_sym: str, sell_amount: float) -> dict:
    addr = TOKENS.get(chain, TOKENS["ethereum"])
    sell = addr.get(sell_sym.upper()); buy = addr.get(buy_sym.upper())
    if not sell or not buy:
        return {"ok": False, "error": "unsupported token"}
    j = await quote_0x(chain, sell, buy, wei(sell_amount))
    if j:
        return {"ok": True, "price": float(j["price"]), "buyAmount": j.get("buyAmount"), "sources": j.get("sources")}
    # offline fallback: basit sentetik fiyat
    # price ~ 2000 (ETH→USDC), diğerleri 1.0
    base_price = 2000.0 if sell_sym.upper()=="ETH" and buy_sym.upper()=="USDC" else 1.0
    return {"ok": True, "price": base_price, "fallback": True}

def tri_opportunity(p_ab: float, p_bc: float, p_ca: float) -> float:
    """ A->B->C->A çarpımı - 1 (pozitifse fırsat). """
    return (p_ab * p_bc * p_ca) - 1.0

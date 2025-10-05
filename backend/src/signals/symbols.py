from __future__ import annotations
import os
import re
from typing import Optional, Dict

# BTCUSDT, BTC/USDT, "BTC usdt", "long sol above 150" gibi formatları yakala
SYM_RE = re.compile(r"\b([A-Z]{3,5})(?:/?USDT)?\b")


def parse_symbol(text: str) -> Optional[str]:
    """Extract raw symbol (e.g. BTC, ETH, SOL) from signal text."""
    text = text.upper()
    m = SYM_RE.search(text)
    if not m:
        return None
    raw = m.group(1)
    return raw


def _load_map() -> Dict[str, str]:
    """Load AUTO_ROUTE_SYMBOL_MAP env as dict."""
    raw = os.getenv("AUTO_ROUTE_SYMBOL_MAP", "")
    out: Dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item or ":" not in item:
            continue
        k, v = item.split(":", 1)
        out[k.strip().upper()] = v.strip()
    return out


def to_cex_symbol(raw: str) -> Optional[str]:
    """Map raw symbol (BTC) to CEX format (BTC/USDT) via env or fallback."""
    m = _load_map()
    if raw.upper() in m:
        return m[raw.upper()]
    # fallback sezgisi
    return f"{raw.upper()}/USDT"




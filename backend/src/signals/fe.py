from __future__ import annotations

import re
from typing import Any

# Bilinen sembol beyaz listesi (genişletilebilir)
KNOWN_SYMBOLS = {
    "BTC",
    "ETH",
    "SOL",
    "AVAX",
    "MATIC",
    "BNB",
    "ADA",
    "DOT",
    "LINK",
    "UNI",
    "ATOM",
    "LTC",
    "XRP",
    "DOGE",
    "SHIB",
    "APT",
    "ARB",
    "OP",
    "SUI",
    "SEI",
    "INJ",
    "TIA",
    "PEPE",
    "WIF",
    "BONK",
    "FET",
    "RNDR",
    "IMX",
    "NEAR",
    "FIL",
}

# Sembol regex: BTC, BTCUSDT, BTC/USDT
SYM = r"(?:[A-Z]{3,6}(?:/USDT|USDT)?)"
RE_SYMS = re.compile(rf"\b({SYM})\b", re.I)

# TP/SL yakala: tp 62000, t/p: 62000, tp=1.25, tp at 1.23 vb.
NUM = r"(\d+(?:\.\d+)?)"
RE_TP = re.compile(
    r"\b(?:tp|t/p|take[\s-]?profit|target)(?:\s+at)?\s*[:=]?\s*" + NUM, re.I
)
RE_SL = re.compile(r"\b(?:sl|s/l|stop[\s-]?loss)(?:\s+at)?\s*[:=]?\s*" + NUM, re.I)

# SIZE: qty 0.5, size 100, notional$ 25, risk 20usd
RE_SIZE = re.compile(
    r"\b(?:size|qty|quantity|notional|risk)\s*[:=]?\s*"
    + NUM
    + r"(?:\s*(?:usd|\$|usdt|dollar|dollars))?",
    re.I,
)


def _norm_symbol(s: str) -> str:
    s = s.upper().replace(" ", "")
    if s.endswith("USDT"):  # BTCUSDT -> BTC/USDT
        base = s[:-4]
        return f"{base}/USDT"
    return s + "/USDT"


def parse_features(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {"symbols": [], "tp": None, "sl": None, "size": None}
    if not text:
        return out
    # symbols (tekil/çoğul) - sadece bilinen semboller
    syms = []
    for m in RE_SYMS.finditer(text.upper()):
        raw = m.group(1).upper()
        # BTCUSDT -> BTC/USDT, BTC/USDT -> BTC/USDT, BTC -> BTC/USDT
        base = raw.replace("/USDT", "").replace("USDT", "")
        if base in KNOWN_SYMBOLS:
            syms.append(_norm_symbol(raw))
    # benzersiz sırayı koru
    seen = set()
    uniq: list[str] = []
    for s in syms:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    out["symbols"] = uniq

    # tp/sl/size
    mtp = RE_TP.search(text)
    msl = RE_SL.search(text)
    msz = RE_SIZE.search(text)
    if mtp:
        out["tp"] = float(mtp.group(1))
    if msl:
        out["sl"] = float(msl.group(1))
    if msz:
        out["size"] = float(msz.group(1))

    return out

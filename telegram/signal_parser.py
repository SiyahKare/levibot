import re

PATTERN = re.compile(
    r"(?P<sym>[A-Z]{3,6}\/?USDT)\b.*?"
    r"(?P<side>LONG|SHORT|BUY|SELL)\b.*?"
    r"(?:entry|e)[:\s]*?(?P<entry>\d+[\.]?\d*)?.*?"
    r"(?:sl|stop)[:\s]*?(?P<sl>\d+[\.]?\d*)?.*?"
    r"(?:tp\d*|take)[:\s]*?(?P<tp>\d+[\.]?\d*)?",
    re.I | re.S,
)


def norm_symbol(s: str) -> str:
    s = s.upper().replace("/", "")
    return s if s.endswith("USDT") else s + "USDT"


def parse_signal(text: str):
    m = PATTERN.search(text or "")
    if not m:
        return None
    g = m.groupdict()
    side = g["side"].upper()
    side = "LONG" if side in ["LONG", "BUY"] else "SHORT"
    sig = {
        "symbol": norm_symbol(g["sym"]),
        "side": side,
        "entry": float(g["entry"]) if g.get("entry") else None,
        "sl": float(g["sl"]) if g.get("sl") else None,
        "tp": float(g["tp"]) if g.get("tp") else None,
    }
    fields = sum(x is not None for x in [sig["entry"], sig["sl"], sig["tp"]])
    confidence = 0.4 + 0.2 * fields
    return {**sig, "confidence": min(confidence, 0.9)}

















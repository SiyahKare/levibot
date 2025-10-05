from __future__ import annotations
import os


def parse_channel_trust() -> dict[str, float]:
    raw = os.getenv("TELEGRAM_CHANNEL_TRUST", "").strip()
    out: dict[str, float] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item or ":" not in item:
            continue
        ch, val = item.split(":", 1)
        try:
            out[ch.strip().lower()] = float(val)
        except Exception:
            continue
    return out


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def adjust_conf(channel: str, conf: float) -> float:
    trust = parse_channel_trust()
    tmin = float(os.getenv("TRUST_MIN", "0.5"))
    tmax = float(os.getenv("TRUST_MAX", "1.5"))
    mult = trust.get((channel or "").lower(), 1.0)
    mult = clamp(mult, tmin, tmax)
    return clamp(conf * mult, 0.0, 0.999)



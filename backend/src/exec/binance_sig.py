from __future__ import annotations

import hmac
import hashlib
import time
import urllib.parse


def sign_params(params: dict, secret: str) -> str:
    qs = urllib.parse.urlencode(params, doseq=True)
    sig = hmac.new(secret.encode(), qs.encode(), hashlib.sha256).hexdigest()
    return qs + "&signature=" + sig


def auth_params(extra: dict | None = None, recv_window: int = 5000) -> dict:
    p = {"timestamp": int(time.time() * 1000), "recvWindow": recv_window}
    if extra:
        p.update(extra)
    return p



















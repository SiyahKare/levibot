from __future__ import annotations
import os, time, threading
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from . import redis_rl

# thread-safe kaydetme
_lock = threading.Lock()
# key -> (window_start_ts, count, burst_tokens)
_state: Dict[str, Tuple[float, int, float]] = {}

def _conf():
    prefixes = [p.strip() for p in os.getenv("SECURED_PATH_PREFIXES", "/signals,/exec,/paper").split(",") if p.strip()]
    api_keys = [k.strip() for k in os.getenv("API_KEYS","").split(",") if k.strip()]
    win = int(os.getenv("RATE_LIMIT_WINDOW_SEC","60"))
    maxi = int(os.getenv("RATE_LIMIT_MAX","120"))
    burst = int(os.getenv("RATE_LIMIT_BURST","40"))
    rl_by = os.getenv("RATE_LIMIT_BY","ip").lower()  # ip|key
    return prefixes, set(api_keys), win, maxi, burst, rl_by

def _token(request: Request, api_key: str | None, rl_by: str) -> str:
    if rl_by == "key" and api_key:
        return f"k:{api_key}"
    # default ip
    ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"

def _is_secured(path: str, prefixes: list[str]) -> bool:
    return any(path.startswith(p) for p in prefixes)

def require_api_key_and_ratelimit():
    async def _mw(request: Request, call_next):
        # Her request'te ENV'i yeniden oku (test uyumluluğu için)
        prefixes, api_keys, win, maxi, burst, rl_by = _conf()
        
        path = request.url.path
        if not _is_secured(path, prefixes):
            return await call_next(request)

        # --- API key (optional) ---
        api_key = request.headers.get("X-API-Key")
        if api_keys and api_key not in api_keys:
            # 401 yerine 403 => key eksik/yanlış
            raise HTTPException(status_code=403, detail="forbidden")

        # --- Rate limit (Redis → fallback in-memory) ---
        token = _token(request, api_key, rl_by)
        
        if redis_rl.enabled():
            # Redis-backed distributed rate limit
            ok, cnt, reset_at = await redis_rl.check_allow(token)
            if not ok:
                raise HTTPException(status_code=429, detail=f"rate limit exceeded; reset_at={reset_at}")
        else:
            # In-memory fallback (sliding window + burst)
            now = time.time()
            with _lock:
                start, cnt, bt = _state.get(token, (now, 0, float(burst)))
                # burst token yenilenmesi (basit: saniyede 1)
                bt = min(float(burst), bt + (now - start))
                # window rollover
                if now - start >= win:
                    start, cnt = now, 0
                # temel limit
                if cnt >= maxi and bt <= 1.0:
                    raise HTTPException(status_code=429, detail="rate limit")
                # tüketim
                cnt += 1
                if cnt > maxi:
                    bt = max(0.0, bt - 1.0)
                _state[token] = (start, cnt, bt)

        return await call_next(request)
    return _mw

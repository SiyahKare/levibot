from __future__ import annotations

import os
from typing import Any


class StateStore:
    """Simple runtime state store.

    Uses Redis if REDIS_URL configured, otherwise in-memory dict.
    """

    def __init__(self) -> None:
        self._redis_url = os.getenv("REDIS_URL")
        self._mem: dict[str, Any] = {}
        self._redis = None
        if self._redis_url:
            try:
                import redis  # type: ignore

                self._redis = redis.Redis.from_url(self._redis_url)
            except Exception:
                self._redis = None

    def get(self, key: str) -> Any | None:
        if self._redis:
            val = self._redis.get(key)
            return val
        return self._mem.get(key)

    def set(self, key: str, value: Any) -> None:
        if self._redis:
            self._redis.set(key, value)
        else:
            self._mem[key] = value

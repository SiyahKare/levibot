from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

CACHE_DIR = Path("data/news_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _key(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def get_cached(text: str) -> dict | None:
    path = CACHE_DIR / f"{_key(text)}.json"
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return None


def set_cached(text: str, obj: Any) -> None:
    path = CACHE_DIR / f"{_key(text)}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)

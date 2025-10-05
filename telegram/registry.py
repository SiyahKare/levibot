import json
import os
import re
from typing import Dict, Any, List
from .config import CHECKPOINTS_PATH, ALLOW_PATTERNS, DENY_PATTERNS


def load_checkpoints() -> Dict[str, Any]:
    if not os.path.exists(CHECKPOINTS_PATH):
        return {}
    with open(CHECKPOINTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_checkpoints(cp: Dict[str, Any]):
    os.makedirs(os.path.dirname(CHECKPOINTS_PATH), exist_ok=True)
    tmp = CHECKPOINTS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cp, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CHECKPOINTS_PATH)


def _match_patterns(text: str, pats: List[str]) -> bool:
    t = (text or "").lower()
    for p in pats:
        if p and re.search(re.escape(p), t):
            return True
    return False


def is_allowed_by_patterns(title: str, username: str | None) -> bool:
    key = f"{title} {('@' + username) if username else ''}"
    if DENY_PATTERNS and _match_patterns(key, DENY_PATTERNS):
        return False
    if not ALLOW_PATTERNS:
        return True
    return _match_patterns(key, ALLOW_PATTERNS)

















from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

CFG_ROOT = Path("backend/configs")
CFG_FILE = CFG_ROOT / "config.yaml"


def load() -> dict[str, Any]:
    if not CFG_FILE.exists():
        return {}
    with open(CFG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def deep_merge(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            deep_merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def save(cfg: dict[str, Any]) -> None:
    CFG_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        "w", delete=False, encoding="utf-8", dir=str(CFG_ROOT)
    )
    try:
        yaml.safe_dump(cfg, tmp, allow_unicode=True, sort_keys=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp.close()
        os.replace(tmp.name, CFG_FILE)
    finally:
        try:
            os.unlink(tmp.name)
        except FileNotFoundError:
            pass

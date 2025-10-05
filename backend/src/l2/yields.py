from __future__ import annotations
from pathlib import Path
import yaml

def list_yields(fp: str | None = None) -> dict:
    p = Path(fp or "backend/configs/yields.yaml")
    if not p.exists():
        return {"ok": True, "chains": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    return {"ok": True, **data}

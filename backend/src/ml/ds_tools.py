from __future__ import annotations

import json
import sys
import time
from pathlib import Path

DATA = Path("backend/data/signals/labels.jsonl")
DATA.parent.mkdir(parents=True, exist_ok=True)

VALID = {"BUY", "SELL", "NO-TRADE"}


def append_label(text: str, label: str) -> None:
    """Append a labeled example to the dataset."""
    label = label.upper().strip()
    assert label in VALID, f"label must be one of {VALID}"
    rec = {"ts": time.time(), "text": text.strip(), "label": label}
    with open(DATA, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def dump_report() -> dict:
    """Generate and print dataset statistics."""
    cnt = {k: 0 for k in VALID}
    n = 0
    if DATA.exists():
        with open(DATA, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    lbl = obj.get("label", "").upper()
                    if lbl in cnt:
                        cnt[lbl] += 1
                        n += 1
                except Exception:
                    continue
    out = {"total": n, "class_counts": cnt}
    print(json.dumps(out, indent=2))
    return out


if __name__ == "__main__":
    # CLI mini: python -m backend.src.ml.ds_tools append "text" BUY
    #           python -m backend.src.ml.ds_tools report
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "append":
        _, _, text, label = sys.argv
        append_label(text, label)
    else:
        dump_report()

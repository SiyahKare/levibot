from __future__ import annotations
from pathlib import Path
import json
import time
from .signal_model import train_and_save

ART = Path("backend/artifacts")
ART.mkdir(parents=True, exist_ok=True)


def main():
    """Train calibrated model and save metrics."""
    model_path = train_and_save()
    metrics = {
        "ts": time.time(),
        "model_path": str(model_path),
        "note": "calibrated LinearSVC (Platt), trained on labels.jsonl",
    }
    with open(ART / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()




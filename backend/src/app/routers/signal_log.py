"""Signal log router - read real signal history from engine logs."""

from __future__ import annotations

import glob
import heapq
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

LOG_DIR = Path("backend/data/logs")
router = APIRouter(prefix="/ops", tags=["ops"])


def _iter_jsonl(path: Path, limit: int) -> Iterator[dict[str, Any]]:
    """
    Iterate through JSONL file backwards, yielding signal events.

    Args:
        path: Path to JSONL log file
        limit: Maximum number of signals to yield

    Yields:
        Signal event dictionaries
    """
    count = 0
    if not path.exists():
        return

    try:
        with path.open() as f:
            lines = list(f)
            for line in reversed(lines):
                try:
                    obj = json.loads(line)
                    # Only yield signal events
                    if obj.get("event") == "signal":
                        yield obj
                        count += 1
                        if count >= limit:
                            return
                except json.JSONDecodeError:
                    continue
    except Exception:
        # Ignore file read errors (file might be locked, missing, etc.)
        return


@router.get("/signal_log")
async def signal_log(limit: int = Query(50, ge=1, le=1000, description="Max signals to return")):
    """
    Get recent signal events from engine logs.

    Reads engine-*.jsonl files and merges them by timestamp.

    Returns:
        List of recent signal events with:
        - ts: timestamp
        - symbol: trading symbol
        - side: long/short/flat
        - prob_up: probability of upward movement
        - source: signal source (e.g. "ensemble")
    """
    # Find all engine log files
    files = glob.glob(str(LOG_DIR / "engine-*.jsonl"))

    # Create iterators for each file
    iters = []
    for fp in files:
        iters.append(_iter_jsonl(Path(fp), limit))

    # Merge by timestamp (descending)
    merged = list(
        heapq.merge(*iters, key=lambda x: x.get("ts", 0), reverse=True)
    )

    # Format output
    out = []
    for item in merged[:limit]:
        out.append(
            {
                "ts": item.get("ts"),
                "symbol": item.get("symbol"),
                "side": item.get("side"),
                "prob_up": item.get("prob_up"),
                "confidence": item.get("confidence"),
                "source": item.get("source", "ensemble"),
            }
        )

    return {"items": out, "total": len(out)}


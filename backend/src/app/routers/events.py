"""
Events router - read engine event history from JSONL logs.
"""
from __future__ import annotations

import glob
import heapq
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

LOG_DIR = Path("backend/data/logs")
router = APIRouter(prefix="/events", tags=["events"])


def _iter_jsonl_events(
    path: Path, event_types: set[str], limit: int
) -> Iterator[dict[str, Any]]:
    """
    Iterate through JSONL file backwards, yielding events matching types.

    Args:
        path: Path to JSONL log file
        event_types: Set of event types to filter (e.g. {"POSITION_CLOSED", "SIGNAL_SCORED"})
        limit: Maximum number of events to yield

    Yields:
        Event dictionaries
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
                    # Check if event type matches (if filtering)
                    if not event_types or obj.get("event") in event_types:
                        yield obj
                        count += 1
                        if count >= limit:
                            return
                except json.JSONDecodeError:
                    continue
    except Exception:
        # Ignore file read errors (file might be locked, missing, etc.)
        return


@router.get("")
async def get_events(
    event_type: str = Query(
        None, description="Event type filter (e.g. POSITION_CLOSED, SIGNAL_SCORED)"
    ),
    limit: int = Query(200, ge=1, le=2000, description="Max events to return"),
):
    """
    Get recent events from engine logs.

    Reads engine-*.jsonl files and merges them by timestamp.

    Query params:
        event_type: Optional filter (comma-separated for multiple, e.g. "SIGNAL_SCORED,POSITION_CLOSED")
        limit: Maximum events to return

    Returns:
        List of event objects (structure varies by event type)
    """
    # Parse event types
    event_types_set: set[str] = set()
    if event_type:
        event_types_set = {t.strip() for t in event_type.split(",") if t.strip()}

    # Find all engine log files
    files = glob.glob(str(LOG_DIR / "engine-*.jsonl"))

    # Create iterators for each file
    iters = []
    for fp in files:
        iters.append(_iter_jsonl_events(Path(fp), event_types_set, limit))

    # Merge by timestamp (descending)
    merged = list(
        heapq.merge(*iters, key=lambda x: x.get("ts", 0), reverse=True)
    )

    # Return raw events (frontend can handle formatting)
    return merged[:limit]


"""Simplified reports.py - minimal working version"""

from __future__ import annotations

import json as _json
import os
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/events")
def events(
    limit: int = 100,
    format: str = Query("json", pattern=r"^(json|jsonl)$"),
    days: int = Query(1, ge=1, le=7),
):
    """Simplified events endpoint - just return recent events"""
    try:
        # Get log base directory
        log_base = Path(os.getenv("LOG_DIR", "/app/backend/data/logs"))

        # Get recent days
        end_dt = datetime.utcnow()
        day_list = [
            (end_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)
        ]

        # Collect files
        files = []
        for d in sorted(day_list, reverse=True):  # Most recent first
            # Root-level YYYY-MM-DD.jsonl files
            root_file = log_base / f"{d}.jsonl"
            if root_file.exists():
                files.append(str(root_file))

            # Directory-level events-*.jsonl files
            day_dir = log_base / d
            if day_dir.exists() and day_dir.is_dir():
                events_files = sorted(day_dir.glob("events-*.jsonl"), reverse=True)
                files.extend([str(f) for f in events_files])

        # Read events
        out = []
        for fp in files:
            try:
                with open(fp, encoding="utf-8") as f:
                    for line in f:
                        try:
                            rec = _json.loads(line)
                            out.append(rec)
                            if len(out) >= limit:
                                break
                        except:
                            continue
                if len(out) >= limit:
                    break
            except:
                continue

        # Sort by timestamp (most recent first)
        out.sort(key=lambda r: r.get("ts") or "", reverse=True)
        out = out[:limit]

    except Exception as e:
        print(f"[/events] ERROR: {e}", flush=True)
        out = []

    if format == "jsonl":
        s = "\n".join(_json.dumps(o, ensure_ascii=False) for o in out) + (
            "\n" if out else ""
        )
        from fastapi.responses import Response

        return Response(s, media_type="application/x-ndjson")

    from fastapi.responses import JSONResponse

    return JSONResponse(content=out)

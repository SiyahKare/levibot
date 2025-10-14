import glob
import gzip
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/analytics", tags=["analytics"])

LOG_DIR = os.getenv("EVENT_LOG_DIR", "backend/data/logs")


def _iter_events(days: int, since_iso: str | None) -> list[dict[str, Any]]:
    since = None
    if since_iso:
        try:
            since = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
        except Exception:
            since = None
    if not since:
        since = datetime.now(UTC) - timedelta(days=days)

    # Gün bazlı dosyaları topla (jsonl ve gz)
    paths = []
    for d in range(days + 1):
        day = (datetime.now(UTC) - timedelta(days=d)).strftime("%Y-%m-%d")
        paths += glob.glob(os.path.join(LOG_DIR, day, "*.jsonl"))
        paths += glob.glob(os.path.join(LOG_DIR, day, "*.jsonl.gz"))

    events = []
    for p in sorted(paths, reverse=True):  # en yeni önce
        opener = gzip.open if p.endswith(".gz") else open
        try:
            with opener(p, "rt", encoding="utf-8") as f:
                for line in f:
                    try:
                        ev = json.loads(line)
                        ts = ev.get("ts")
                        # ts: ISO string veya epoch olabilir
                        if isinstance(ts, (int, float)):
                            ev_dt = datetime.fromtimestamp(ts, tz=UTC)
                        else:
                            ev_dt = datetime.fromisoformat(
                                str(ts).replace("Z", "+00:00")
                            )
                        if ev_dt >= since:
                            events.append(ev)
                    except Exception:
                        continue
        except FileNotFoundError:
            continue
    return events


@router.get("/stats")
def analytics_stats(
    days: int = Query(1, ge=1, le=30),
    since_iso: str | None = Query(None),
    event_type: str | None = Query(None),
):
    """
    Event distribution statistics.

    Returns aggregated counts by event type and symbol.
    """
    evs = _iter_events(days, since_iso)
    if event_type:
        types = {t.strip() for t in event_type.split(",")}
        evs = [e for e in evs if e.get("event_type") in types]

    type_counts: dict[str, int] = {}
    symbols: dict[str, int] = {}
    total = 0

    for e in evs:
        total += 1
        t = e.get("event_type", "UNKNOWN")
        type_counts[t] = type_counts.get(t, 0) + 1
        sym = (e.get("payload", {}) or {}).get("symbol")
        if sym:
            symbols[sym] = symbols.get(sym, 0) + 1

    return {"total": total, "event_types": type_counts, "symbols": symbols}


def _bucket_key(dt: datetime, interval: str) -> datetime:
    if interval == "1m":
        return dt.replace(second=0, microsecond=0)
    if interval == "5m":
        minute = (dt.minute // 5) * 5
        return dt.replace(minute=minute, second=0, microsecond=0)
    if interval == "15m":
        minute = (dt.minute // 15) * 15
        return dt.replace(minute=minute, second=0, microsecond=0)
    if interval == "1h":
        return dt.replace(minute=0, second=0, microsecond=0)
    return dt


@router.get("/timeseries")
def analytics_timeseries(
    interval: str = Query("5m", pattern="^(1m|5m|15m|1h)$"),
    days: int = Query(1, ge=1, le=30),
    since_iso: str | None = Query(None),
    event_type: str | None = Query(None),
):
    """
    Time-series event counts bucketed by interval.

    Supported intervals: 1m, 5m, 15m, 1h
    """
    evs = _iter_events(days, since_iso)
    if event_type:
        types = {t.strip() for t in event_type.split(",")}
        evs = [e for e in evs if e.get("event_type") in types]

    buckets: dict[str, int] = {}
    for e in evs:
        ts = e.get("ts")
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=UTC)
        else:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        key = _bucket_key(dt, interval).isoformat()
        buckets[key] = buckets.get(key, 0) + 1

    series = [{"ts": k, "count": buckets[k]} for k in sorted(buckets.keys())]
    return {"interval": interval, "points": series}


@router.get("/traces")
def analytics_traces(
    days: int = Query(1, ge=1, le=30),
    since_iso: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
):
    """
    Top active traces ranked by event count and duration.

    Returns trace metadata including event count, first/last timestamps, and duration.
    """
    evs = _iter_events(days, since_iso)
    groups: dict[str, dict[str, Any]] = {}
    for e in evs:
        trace = e.get("trace_id")
        if not trace:
            continue
        ts = e.get("ts")
        if isinstance(ts, (int, float)):
            dt = datetime.fromtimestamp(ts, tz=UTC)
        else:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        g = groups.setdefault(
            trace, {"trace_id": trace, "event_count": 0, "first_ts": dt, "last_ts": dt}
        )
        g["event_count"] += 1
        if dt < g["first_ts"]:
            g["first_ts"] = dt
        if dt > g["last_ts"]:
            g["last_ts"] = dt

    rows = []
    for g in groups.values():
        rows.append(
            {
                "trace_id": g["trace_id"],
                "event_count": g["event_count"],
                "first_ts": g["first_ts"].isoformat(),
                "last_ts": g["last_ts"].isoformat(),
                "duration_sec": max(
                    0, int((g["last_ts"] - g["first_ts"]).total_seconds())
                ),
            }
        )
    rows.sort(key=lambda r: (r["event_count"], r["duration_sec"]), reverse=True)
    return {"total": len(rows), "rows": rows[:limit]}

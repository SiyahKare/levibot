from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Response, Query
import duckdb
from ..infra import duck as duckinfra
import io
import polars as pl
import glob
import json as _json


router = APIRouter()


def _export_json(data: dict) -> Response:
    from fastapi.responses import JSONResponse
    return JSONResponse(content=data)


@router.get("/reports/daily")
def daily(date: Optional[str] = None, format: str = Query("json", pattern=r"^(json|csv|parquet)$")):
    # Doğrudan read_json_auto ile sorgula (CREATE VIEW ve prepared param gerektirme)
    con = duckdb.connect()
    day = date or datetime.utcnow().strftime("%Y-%m-%d")
    pattern = duckinfra._glob_for_day(day)
    if not glob.glob(pattern):
        pnl = 0.0
        trades = 0
        by_symbol = []
    else:
        pnl = 0.0  # pnl_usdt yok, smoke için 0
        trades = con.sql(f"""
            SELECT count(*) FROM read_json_auto('{pattern}') 
            WHERE event_type='POSITION_CLOSED'
        """).fetchone()[0]
        by_symbol = con.sql(f"""
            SELECT symbol, count(*) AS trades, 0.0 AS pnl
            FROM read_json_auto('{pattern}')
            WHERE event_type='POSITION_CLOSED' AND symbol IS NOT NULL
            GROUP BY symbol
        """).fetchall()
    # trades ve by_symbol yukarıda hesaplandı
    data = {
        "date": (date or datetime.utcnow().strftime("%Y-%m-%d")),
        "users": ["onur"],
        "summary": {
            "pnl_usdt": pnl,
            "hit_rate": None,
            "avg_win": None,
            "avg_loss": None,
            "max_dd_pct": None,
            "fees_usdt": None,
            "funding_usdt": None,
            "trades": trades,
        },
        "by_symbol": [
            {"symbol": r[0], "trades": int(r[1]), "pnl": float(r[2])} for r in by_symbol
        ],
    }
    if format == "json":
        return _export_json(data)
    df = pl.DataFrame(data["by_symbol"]) if data["by_symbol"] else pl.DataFrame({"symbol": [], "trades": [], "pnl": []})
    if format == "csv":
        buf = io.StringIO()
        buf.write(df.write_csv())
        return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=daily_{date or 'today'}.csv"})
    # parquet
    bbuf = io.BytesIO()
    df.write_parquet(bbuf)
    return Response(bbuf.getvalue(), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename=daily_{date or 'today'}.parquet"})


@router.get("/reports/weekly")
def weekly(end: Optional[str] = None, format: str = Query("json", pattern=r"^(json|csv|parquet)$")):
    # Haftalık: mevcut günlerin path'lerini topla ve SQL'i birleştir
    con = duckdb.connect()
    end_dt = datetime.strptime(end, "%Y-%m-%d") if end else datetime.utcnow()
    days = [(end_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    parts = []
    for d in days:
        pat = duckinfra._glob_for_day(d)
        if glob.glob(pat):
            # Sadece gerekli alanları projekte et, payload'ı dahil etme
            parts.append(f"SELECT substr(ts, 1, 10) AS date FROM read_json_auto('{pat}') WHERE event_type='POSITION_CLOSED'")
    pnl = 0.0
    if parts:
        union_sql = " UNION ALL ".join(parts)
        trades_by_day = con.sql(
            f"""
            SELECT date, count(*) AS trades
            FROM ({union_sql}) u
            GROUP BY date
            ORDER BY date
            """
        ).fetchall()
    else:
        trades_by_day = []
    data = {
        "week": None,
        "pnl_usdt": pnl,
        "max_dd_pct": None,
        "by_day": [{"date": r[0], "pnl": 0.0} for r in trades_by_day],
        "trades_by_day": [{"date": r[0], "trades": int(r[1])} for r in trades_by_day],
        "regime_dist": None,
        "top_win_symbols": None,
        "worst_symbols": None,
    }
    if format == "json":
        return _export_json(data)
    df = pl.DataFrame(data["by_day"]) if data["by_day"] else pl.DataFrame({"date": [], "pnl": []})
    if format == "csv":
        buf = io.StringIO()
        buf.write(df.write_csv())
        return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=weekly_{end or 'today'}.csv"})
    bbuf = io.BytesIO()
    df.write_parquet(bbuf)
    return Response(bbuf.getvalue(), media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename=weekly_{end or 'today'}.parquet"})


@router.get("/events")
def events(
    limit: int = Query(200, ge=1, le=1000),
    format: str = Query("json", pattern=r"^(json|jsonl)$"),
    days: int = Query(1, ge=1, le=7),
    event_type: Optional[str] = None,
    symbol: Optional[str] = None,
    trace_id: Optional[str] = None,
    since_iso: Optional[str] = None,
    q: Optional[str] = None,
):
    """
    Smart event filtering endpoint
    
    Filters (all optional):
    - event_type: CSV list (e.g., "SIGNAL_SCORED,POSITION_CLOSED")
    - symbol: Exact match (e.g., "BTCUSDT")
    - trace_id: Exact match (for debugging)
    - since_iso: ISO timestamp (e.g., "2025-10-06T00:00:00Z")
    - q: Full-text search in payload (case-insensitive)
    - limit: Max results (default 200, max 1000)
    - days: Days to look back (default 1, max 7)
    """
    try:
        # Get log base directory
        import os
        from pathlib import Path
        log_base = Path(os.getenv("LOG_DIR", "/app/backend/data/logs"))
        
        # Get recent days
        end_dt = datetime.utcnow()
        day_list = [(end_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        
        # Collect files (most recent first)
        files = []
        for d in sorted(day_list, reverse=True):
            # Root-level YYYY-MM-DD.jsonl files
            root_file = log_base / f"{d}.jsonl"
            if root_file.exists():
                files.append(str(root_file))
            
            # Directory-level events-*.jsonl files
            day_dir = log_base / d
            if day_dir.exists() and day_dir.is_dir():
                events_files = sorted(day_dir.glob("events-*.jsonl"), reverse=True)
                files.extend([str(f) for f in events_files])
        
        # Prepare filters
        allowed_types = None
        if event_type:
            allowed_types = {t.strip() for t in event_type.split(",") if t.strip()}
        
        q_lower = q.lower() if q else None
        since = since_iso or "1970-01-01T00:00:00Z"
        
        # Read and filter events
        out = []
        for fp in files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            rec = _json.loads(line)
                        except:
                            continue
                        
                        # Apply filters
                        if allowed_types and rec.get("event_type") not in allowed_types:
                            continue
                        
                        if symbol and rec.get("symbol") != symbol:
                            continue
                        
                        if trace_id and rec.get("trace_id") != trace_id:
                            continue
                        
                        ts = rec.get("ts") or ""
                        if ts < since:
                            continue
                        
                        if q_lower:
                            # Full-text search in payload
                            try:
                                payload_str = _json.dumps(rec.get("payload", {}), ensure_ascii=False).lower()
                                event_type_str = (rec.get("event_type") or "").lower()
                                symbol_str = (rec.get("symbol") or "").lower()
                                trace_str = (rec.get("trace_id") or "").lower()
                                combined = f"{event_type_str} {symbol_str} {trace_str} {payload_str}"
                                if q_lower not in combined:
                                    continue
                            except:
                                continue
                        
                        out.append(rec)
                        if len(out) >= limit:
                            break
                
                if len(out) >= limit:
                    break
            except:
                continue
        
        # Sort by timestamp (most recent first)
        out.sort(key=lambda r: r.get("ts") or "", reverse=True)
        out = out[:limit]
        
    except Exception as e:
        import sys
        print(f"[/events] ERROR: {e}", file=sys.stderr, flush=True)
        out = []
    
    if format == "jsonl":
        s = "\n".join(_json.dumps(o, ensure_ascii=False) for o in out) + ("\n" if out else "")
        return Response(s, media_type="application/x-ndjson")
    from fastapi.responses import JSONResponse
    return JSONResponse(content=out)



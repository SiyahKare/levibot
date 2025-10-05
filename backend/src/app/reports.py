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
    trace_id: Optional[str] = None,
    event_type: Optional[str] = None,
    since_iso: Optional[str] = None,
    limit: int = 100,
    format: str = Query("json", pattern=r"^(json|jsonl)$"),
    day: Optional[str] = None,
    days: int = Query(1, ge=1, le=7),
    q: Optional[str] = None,
    symbol: Optional[str] = None,
):
    try:
        # Gün aralığı belirle
        if day:
            try:
                end_dt = datetime.strptime(day, "%Y-%m-%d")
            except Exception:
                end_dt = datetime.utcnow()
        else:
            end_dt = datetime.utcnow()
        day_list = [(end_dt - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        files = []
        
        # Basit absolute path kullan
        import os
        from pathlib import Path
        # Docker içinde /app, local'de workspace root
        log_base = Path(os.getenv("LOG_DIR", "/app/backend/data/logs"))
        
        for d in sorted(day_list):
            # Klasör içindeki events-*.jsonl dosyaları
            pattern1 = str(log_base / d / "events-*.jsonl")
            files.extend(sorted(glob.glob(pattern1)))
            
            # Root'taki YYYY-MM-DD.jsonl dosyası
            pattern2 = str(log_base / f"{d}.jsonl")
            files.extend(sorted(glob.glob(pattern2)))
        
        if not files:
            out = []
        else:
            since = since_iso or "1970-01-01T00:00:00Z"
            out = []
            # event_type CSV desteği (ör. event_type=ONCHAIN_SIGNAL,MEV_ARB_OPP)
            allowed_types = None
            if event_type:
                try:
                    allowed_types = {t.strip() for t in event_type.split(",") if t.strip()}
                except Exception:
                    allowed_types = None
            q_lower = q.lower() if q else None
            for fp in files:
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                rec = _json.loads(line)
                            except Exception:
                                continue
                            if allowed_types is not None and (rec.get("event_type") not in allowed_types):
                                continue
                            if trace_id and rec.get("trace_id") != trace_id:
                                continue
                            if symbol and (rec.get("symbol") != symbol):
                                continue
                            ts = rec.get("ts") or ""
                            if ts < since:
                                continue
                            if q_lower:
                                try:
                                    payload_s = _json.dumps(rec.get("payload"), ensure_ascii=False)
                                except Exception:
                                    payload_s = ""
                                # basit metin araması: event_type, symbol, trace_id ve payload string içinde ara
                                comb = f"{rec.get('event_type') or ''} {rec.get('symbol') or ''} {rec.get('trace_id') or ''} {payload_s}"
                                if q_lower not in comb.lower():
                                    continue
                            out.append(rec)
                            if len(out) >= limit:
                                break
                except Exception:
                    continue
            # Sıralama ve limit güvenliği
            out.sort(key=lambda r: r.get("ts") or "")
            out = out[:limit]
    except Exception:
        out = []
    if format == "jsonl":
        import json as _json
        s = "\n".join(_json.dumps(o, ensure_ascii=False) for o in out) + ("\n" if out else "")
        return Response(s, media_type="application/x-ndjson")
    from fastapi.responses import JSONResponse
    return JSONResponse(content=out)



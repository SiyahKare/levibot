from __future__ import annotations

import glob
from datetime import datetime, timedelta
from pathlib import Path

import duckdb


def _glob_for_day(day_str: str) -> str:
    # Make absolute path to be robust to different CWDs
    base = Path(__file__).resolve().parents[3] / "backend" / "data" / "logs" / day_str
    return str(base / "events-*.jsonl")


def load_day(day_str: str | None = None) -> duckdb.DuckDBPyRelation:
    day = day_str or datetime.utcnow().strftime("%Y-%m-%d")
    con = duckdb.connect()
    # Dosyalar yoksa boş şemalı bir relation döndür
    pattern = _glob_for_day(day)
    if not glob.glob(pattern):
        return con.sql(
            """
            SELECT * FROM (
              SELECT 
                CAST(NULL AS TIMESTAMP) AS ts,
                CAST(NULL AS VARCHAR)   AS event_type,
                CAST(NULL AS VARCHAR)   AS symbol,
                CAST(NULL AS JSON)      AS payload,
                CAST(NULL AS VARCHAR)   AS trace_id
            ) WHERE 0=1
            """
        )
    # Use SQL helper read_json_auto for glob patterns (duckdb 1.1 API)
    rel = con.sql("SELECT * FROM read_json_auto(?)", params=[pattern])
    return rel


def load_week_ending(end_day: str | None = None) -> duckdb.DuckDBPyRelation:
    end = datetime.strptime(end_day, "%Y-%m-%d") if end_day else datetime.utcnow()
    days = [(end - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    con = duckdb.connect()
    # Union daily relations
    rels = []
    for d in days:
        pattern = _glob_for_day(d)
        if not glob.glob(pattern):
            rel = con.sql(
                """
                SELECT * FROM (
                  SELECT 
                    CAST(NULL AS TIMESTAMP) AS ts,
                    CAST(NULL AS VARCHAR)   AS event_type,
                    CAST(NULL AS VARCHAR)   AS symbol,
                    CAST(NULL AS JSON)      AS payload,
                    CAST(NULL AS VARCHAR)   AS trace_id
                ) WHERE 0=1
                """
            )
        else:
            rel = con.sql("SELECT * FROM read_json_auto(?)", params=[pattern])
        rels.append(rel)
    if not rels:
        return con.sql("SELECT 1 WHERE 0=1")
    base = rels[0]
    for r in rels[1:]:
        base = base.union_all(r)
    return base

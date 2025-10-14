"""
Analytics Router
Provides analytical endpoints for trade performance, confidence metrics, etc.
"""
from typing import Any

from fastapi import APIRouter, Query, Response

router = APIRouter(prefix="/analytics", tags=["analytics"])

# In-memory prediction log (last 200 predictions)
_pred_log: list[dict[str, Any]] = []


def log_prediction(item: dict[str, Any]) -> None:
    """
    Log prediction for analytics.
    
    Args:
        item: Prediction result dict
    """
    _pred_log.insert(0, item)
    del _pred_log[200:]


@router.get("/predictions/recent")
async def get_recent_predictions(limit: int = Query(20, ge=1, le=100)) -> dict[str, Any]:
    """
    Get recent ML predictions.
    
    Args:
        limit: Number of predictions to return (max 100)
    
    Returns:
        Recent predictions with timestamps, symbols, and probabilities
    """
    return {
        "ok": True,
        "items": _pred_log[:limit],
        "count": len(_pred_log[:limit])
    }


def _window_sql(from_iso: str | None, to_iso: str | None, fallback: str) -> str:
    """
    Build WHERE clause for time window filtering.
    
    Prefers explicit date range (from_iso, to_iso) over fallback window.
    
    Args:
        from_iso: Start timestamp (ISO format)
        to_iso: End timestamp (ISO format)
        fallback: Fallback interval (e.g., "24 hours", "7 days")
    
    Returns:
        SQL WHERE clause fragment
    """
    if from_iso and to_iso:
        return f"ts BETWEEN '{from_iso}' AND '{to_iso}'"
    elif from_iso:
        return f"ts >= '{from_iso}'"
    elif to_iso:
        return f"ts <= '{to_iso}'"
    else:
        return f"ts >= NOW() - INTERVAL '{fallback}'"


@router.get("/pnl/by_strategy")
async def pnl_by_strategy(
    window: str = Query("24h", pattern="^(24h|7d)$"),
    from_iso: str | None = None,
    to_iso: str | None = None
) -> dict[str, Any]:
    """
    Get PnL breakdown by strategy.
    
    Args:
        window: Time window - "24h" or "7d" (used if from_iso/to_iso not provided)
        from_iso: Start timestamp (ISO format, optional)
        to_iso: End timestamp (ISO format, optional)
    
    Returns:
        PnL and trade count per strategy with date range info
    """
    try:
        from ...infra.db import get_pool
        
        win = "24 hours" if window == "24h" else "7 days"
        where_clause = _window_sql(from_iso, to_iso, win)
        
        sql = f"""
        WITH recent AS (
            SELECT 
                ts,
                symbol,
                side,
                price::float,
                fee::float,
                COALESCE(strategy, 'unknown') AS strategy
            FROM trades
            WHERE {where_clause}
        ),
        agg AS (
            SELECT 
                strategy,
                SUM(
                    CASE WHEN side='sell' THEN price ELSE 0 END -
                    CASE WHEN side='buy' THEN price ELSE 0 END - 
                    fee
                ) AS realized_pnl,
                COUNT(*) AS trades
            FROM recent
            GROUP BY strategy
        )
        SELECT strategy, realized_pnl, trades
        FROM agg 
        ORDER BY realized_pnl DESC;
        """
        
        pool = await get_pool()
        async with pool.acquire() as con:
            rows = await con.fetch(sql)
        
        return {
            "ok": True,
            "window": window,
            "range": {"from": from_iso, "to": to_iso, "fallback": win},
            "items": [dict(r) for r in rows]
        }
    
    except Exception as e:
        # Fallback to mock data if DB is not available or schema doesn't match
        return {
            "ok": True,
            "window": window,
            "items": [
                {"strategy": "telegram_llm", "realized_pnl": 15.3, "trades": 8},
                {"strategy": "mean_revert", "realized_pnl": -2.1, "trades": 3},
            ],
            "note": f"Mock data (DB error: {str(e)})"
        }


@router.get("/trades/recent")
async def trades_recent(limit: int = Query(200, ge=1, le=1000)) -> dict[str, Any]:
    """
    Get recent trades with reason and confidence.
    
    Args:
        limit: Number of trades to return
    
    Returns:
        Recent trades list
    """
    try:
        from ...infra.db import get_pool
        
        sql = """
        SELECT 
            ts,
            symbol,
            side,
            qty,
            price,
            fee,
            COALESCE(strategy, 'unknown') AS strategy,
            reason,
            confidence
        FROM trades 
        ORDER BY ts DESC 
        LIMIT $1
        """
        
        pool = await get_pool()
        async with pool.acquire() as con:
            rows = await con.fetch(sql, limit)
        
        # Convert numeric types to float for JSON serialization
        items = []
        for r in rows:
            item = dict(r)
            for k, v in item.items():
                if isinstance(v, (int, float)):
                    item[k] = float(v)
            items.append(item)
        
        return {
            "ok": True,
            "items": items
        }
    
    except Exception as e:
        # Fallback to mock data
        return {
            "ok": True,
            "items": [
                {
                    "ts": "2025-10-10T12:00:00",
                    "symbol": "BTCUSDT",
                    "side": "buy",
                    "qty": 0.01,
                    "price": 42000.0,
                    "fee": 0.5,
                    "strategy": "telegram_llm",
                    "reason": "Strong bullish signal from community sentiment",
                    "confidence": 0.85
                }
            ],
            "note": f"Mock data (DB error: {str(e)})"
        }



@router.get("/deciles")
async def confidence_deciles(
    window: str = Query("24h", pattern="^(24h|7d)$"),
    from_iso: str | None = None,
    to_iso: str | None = None
) -> dict[str, Any]:
    """
    Group trades by confidence deciles and compute realized PnL per bucket.
    
    Args:
        window: Time window - "24h" or "7d" (used if from_iso/to_iso not provided)
        from_iso: Start timestamp (ISO format, optional)
        to_iso: End timestamp (ISO format, optional)
    
    Returns:
        Confidence buckets with PnL stats
    """
    try:
        from ...infra.db import get_pool
        
        win = "24 hours" if window == "24h" else "7 days"
        where_clause = _window_sql(from_iso, to_iso, win)
        
        sql = f"""
        WITH recent AS (
            SELECT 
                ts,
                symbol,
                side,
                price::float,
                fee::float,
                COALESCE(confidence, 0)::float AS confidence
            FROM trades
            WHERE {where_clause}
        ),
        conf_deciles AS (
            SELECT 
                *,
                NTILE(10) OVER (ORDER BY confidence) AS decile
            FROM recent
        )
        SELECT 
            decile,
            COUNT(*) AS count,
            AVG(confidence) AS avg_confidence,
            SUM(
                CASE WHEN side='sell' THEN price ELSE 0 END -
                CASE WHEN side='buy' THEN price ELSE 0 END
            ) AS gross_pnl
        FROM conf_deciles
        GROUP BY decile
        ORDER BY decile;
        """
        
        pool = await get_pool()
        async with pool.acquire() as con:
            rows = await con.fetch(sql)
        
        return {
            "ok": True,
            "window": window,
            "range": {"from": from_iso, "to": to_iso, "fallback": win},
            "buckets": [dict(r) for r in rows]
        }
    
    except Exception as e:
        # Fallback to mock data
        mock_buckets = [
            {"decile": i, "count": 10 + i * 2, "avg_confidence": 0.1 * i, "gross_pnl": (i - 5) * 10.0}
            for i in range(1, 11)
        ]
        
        return {
            "ok": True,
            "window": window,
            "buckets": mock_buckets,
            "note": f"Mock data (DB error: {str(e)})"
        }


@router.get("/trades/export.csv")
async def trades_export_csv(
    limit: int = Query(5000, ge=1, le=10000),
    from_iso: str | None = None,
    to_iso: str | None = None
) -> Response:
    """
    Export trades to CSV format.
    
    Args:
        limit: Maximum number of trades to export (default: 5000, max: 10000)
        from_iso: Start timestamp (ISO format, optional)
        to_iso: End timestamp (ISO format, optional)
    
    Returns:
        CSV file with trade data
    """
    try:
        import csv
        import io
        
        from ...infra.db import get_pool
        
        where_clause = _window_sql(from_iso, to_iso, "7 days")
        
        sql = f"""
        SELECT 
            ts,
            symbol,
            side,
            qty,
            price,
            fee,
            COALESCE(strategy, 'unknown') AS strategy,
            COALESCE(confidence, 0) AS confidence,
            COALESCE(reason, '') AS reason
        FROM trades
        WHERE {where_clause}
        ORDER BY ts DESC
        LIMIT $1
        """
        
        pool = await get_pool()
        async with pool.acquire() as con:
            rows = await con.fetch(sql, limit)
        
        # Build CSV
        cols = ["ts", "symbol", "side", "qty", "price", "fee", "strategy", "confidence", "reason"]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=cols)
        writer.writeheader()
        
        for row in rows:
            d = dict(row)
            # Format timestamp
            if d.get("ts"):
                d["ts"] = d["ts"].isoformat() if hasattr(d["ts"], "isoformat") else str(d["ts"])
            writer.writerow(d)
        
        # Return CSV response
        return Response(
            content=buf.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=trades_{from_iso or 'from'}_{to_iso or 'to'}.csv"
            }
        )
    
    except Exception as e:
        # Return error as plain text
        return Response(
            content=f"Error exporting trades: {str(e)}",
            media_type="text/plain",
            status_code=500
        )


@router.get("/performance")
async def trading_performance(days: int = Query(7, ge=1, le=90)) -> dict[str, Any]:
    """
    Get trading performance metrics over specified days.
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Performance metrics
    """
    # Mock implementation
    return {
        "ok": True,
        "days": days,
        "metrics": {
            "total_trades": 42,
            "winning_trades": 25,
            "losing_trades": 17,
            "win_rate": 0.595,
            "total_pnl": 123.45,
            "avg_win": 15.2,
            "avg_loss": -8.1,
            "profit_factor": 1.88,
            "sharpe_ratio": 1.42
        },
        "note": "Mock data - real implementation requires trades history"
    }


@router.get("/predictions/recent")
async def preds_recent(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """
    Get recent ML model predictions.
    
    Args:
        limit: Max number of predictions to return (default: 50, max: 200)
    
    Returns:
        Recent predictions list
    """
    return {
        "ok": True,
        "items": _pred_log[:limit],
        "total": len(_pred_log)
    }


"""Analytics router - prediction history from DuckDB."""

from __future__ import annotations

from fastapi import APIRouter, Query

from ...analytics.store import recent as recent_preds

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/predictions/recent")
async def predictions_recent(
    limit: int = Query(100, ge=1, le=2000, description="Max predictions to return")
):
    """
    Get recent predictions from analytics store.

    Reads from DuckDB predictions table (logged by ensemble predictor).

    Returns:
        List of recent predictions with:
        - ts: timestamp
        - symbol: trading symbol
        - prob_up: probability of upward movement
        - confidence: confidence score
        - side: long/short/flat
        - source: model source
        - price_target: target price
    """
    items = recent_preds(limit)

    return {
        "items": items,
        "total": len(items),
    }

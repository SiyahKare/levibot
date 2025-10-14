"""
AI Brain API Endpoints
Provides OpenAI-powered features: news scoring, regime advice, anomaly detection
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..ai.openai_client import (
    explain_anomaly,
    regime_advice,
    score_headline,
    score_headlines,
)
from ..infra.logger import log_event

router = APIRouter()


class NewsScoreRequest(BaseModel):
    headline: str


class NewsScoreBatchRequest(BaseModel):
    headlines: list[str]


class RegimeAdviceRequest(BaseModel):
    metrics: dict[str, Any]


class AnomalyExplainRequest(BaseModel):
    context: dict[str, Any]


@router.post("/ai/news/score")
async def ai_news_score(req: NewsScoreRequest) -> dict[str, Any]:
    """
    Score a single news headline for crypto impact using OpenAI.

    Returns: {asset, event_type, impact, horizon, confidence}
    """
    if not req.headline.strip():
        raise HTTPException(status_code=400, detail="headline cannot be empty")

    try:
        result = score_headline(req.headline)
        log_event("AI_NEWS_SCORE", {"headline": req.headline, "result": result})
        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(
            status_code=503, detail=f"OpenAI service unavailable: {str(e)}"
        )
    except Exception as e:
        log_event("ERROR", {"scope": "ai_news_score", "error": str(e)})
        raise HTTPException(status_code=500, detail=f"News scoring failed: {str(e)}")


@router.post("/ai/news/score-batch")
async def ai_news_score_batch(req: NewsScoreBatchRequest) -> dict[str, Any]:
    """
    Score multiple news headlines for crypto impact using OpenAI.

    Returns: {ok, results: [{asset, event_type, impact, horizon, confidence}, ...]}
    """
    if not req.headlines:
        raise HTTPException(status_code=400, detail="headlines cannot be empty")

    if len(req.headlines) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 headlines allowed")

    try:
        results = score_headlines(req.headlines)
        log_event(
            "AI_NEWS_SCORE_BATCH", {"count": len(req.headlines), "results": results}
        )
        return {"ok": True, "results": results}
    except ValueError as e:
        raise HTTPException(
            status_code=503, detail=f"OpenAI service unavailable: {str(e)}"
        )
    except Exception as e:
        log_event("ERROR", {"scope": "ai_news_score_batch", "error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Batch news scoring failed: {str(e)}"
        )


@router.post("/ai/regime/advice")
async def ai_regime_advice(req: RegimeAdviceRequest) -> dict[str, Any]:
    """
    Get regime-based trading advice from OpenAI.

    Args:
        metrics: Current market metrics (volatility, trend, ECE, PSI, PnL, etc.)

    Returns: {regime, risk_multiplier, entry_delta, exit_delta, reason}
    """
    if not req.metrics:
        raise HTTPException(status_code=400, detail="metrics cannot be empty")

    try:
        result = regime_advice(req.metrics)
        log_event("AI_REGIME_ADVICE", {"metrics": req.metrics, "advice": result})
        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(
            status_code=503, detail=f"OpenAI service unavailable: {str(e)}"
        )
    except Exception as e:
        log_event("ERROR", {"scope": "ai_regime_advice", "error": str(e)})
        raise HTTPException(status_code=500, detail=f"Regime advice failed: {str(e)}")


@router.post("/ai/anomaly/explain")
async def ai_anomaly_explain(req: AnomalyExplainRequest) -> dict[str, Any]:
    """
    Explain an anomaly and provide runbook suggestions using OpenAI.

    Args:
        context: Anomaly context (PSI, ECE, PnL, staleness, etc.)

    Returns: {cause, runbook, severity}
    """
    if not req.context:
        raise HTTPException(status_code=400, detail="context cannot be empty")

    try:
        result = explain_anomaly(req.context)
        log_event("AI_ANOMALY_EXPLAIN", {"context": req.context, "explanation": result})
        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(
            status_code=503, detail=f"OpenAI service unavailable: {str(e)}"
        )
    except Exception as e:
        log_event("ERROR", {"scope": "ai_anomaly_explain", "error": str(e)})
        raise HTTPException(
            status_code=500, detail=f"Anomaly explanation failed: {str(e)}"
        )

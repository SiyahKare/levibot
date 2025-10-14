"""
AI Brain API Router
Endpoints for OpenAI-powered decision support
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from ...ai.openai_client import explain_anomaly, regime_advice, score_headlines

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/score_news")
async def score_news_endpoint(
    headlines: list[str],
) -> dict[str, Any]:
    """
    Score news headlines for crypto impact.

    Args:
        headlines: List of news headline texts

    Returns:
        Scored headlines with structured impact data
    """
    if not headlines:
        raise HTTPException(status_code=400, detail="No headlines provided")

    if len(headlines) > 20:
        raise HTTPException(status_code=400, detail="Max 20 headlines per request")

    try:
        scores = score_headlines(headlines)
        return {
            "ok": True,
            "count": len(scores),
            "scores": scores,
        }
    except ValueError as e:
        # OpenAI API key not set
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI scoring failed: {str(e)}")


@router.post("/regime")
async def regime_endpoint(
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """
    Get regime-based trading advice.

    Args:
        metrics: Current market metrics

    Returns:
        Regime advice with risk adjustments
    """
    if not metrics:
        raise HTTPException(status_code=400, detail="No metrics provided")

    try:
        advice = regime_advice(metrics)
        return {
            "ok": True,
            "advice": advice,
        }
    except ValueError as e:
        # OpenAI API key not set
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regime analysis failed: {str(e)}")


@router.post("/explain")
async def explain_endpoint(
    context: dict[str, Any],
) -> dict[str, Any]:
    """
    Explain an anomaly and get runbook suggestions.

    Args:
        context: Anomaly context (PSI, ECE, PnL, etc.)

    Returns:
        Explanation with cause, runbook, and severity
    """
    if not context:
        raise HTTPException(status_code=400, detail="No context provided")

    try:
        explanation = explain_anomaly(context)
        return {
            "ok": True,
            "explanation": explanation,
        }
    except ValueError as e:
        # OpenAI API key not set
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")


@router.get("/status")
async def ai_status() -> dict[str, Any]:
    """Get AI Brain status."""
    import os

    return {
        "ok": True,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "cache_enabled": True,
        "models": {
            "news_scoring": "gpt-4o-mini",
            "regime_advice": "gpt-4o-mini",
            "explainer": "gpt-4o-mini",
        },
    }

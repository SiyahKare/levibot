"""
Prometheus metrics endpoint.
"""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

router = APIRouter(tags=["metrics"])


@router.get("/metrics/prom")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.

    Exposes all LeviBot metrics in Prometheus format.

    Usage:
        curl http://localhost:8000/metrics/prom
    """
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

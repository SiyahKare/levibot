"""
Server-Sent Events (SSE) endpoints for real-time updates.
"""

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...engine.manager import get_engine_manager

router = APIRouter(prefix="/stream", tags=["stream"])


async def engine_status_generator():
    """
    Generate engine status updates every 2 seconds.
    
    Yields JSON messages with engine metrics.
    """
    while True:
        try:
            manager = get_engine_manager()
            
            # Send status for each engine
            for symbol, eng in manager.engines.items():
                data = {
                    "symbol": symbol,
                    "status": "running",  # All registered engines are running
                    "inference_p95_ms": 0.0,  # TODO: collect from metrics
                    "uptime_s": 0.0,  # TODO: track uptime
                    "trades_today": 0,  # TODO: track trades
                }
                
                yield f"data: {json.dumps(data)}\n\n"
            
            await asyncio.sleep(2)  # Update every 2 seconds
            
        except RuntimeError:
            # Manager not initialized yet
            yield f"data: {json.dumps({'error': 'initializing'})}\n\n"
            await asyncio.sleep(5)
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(5)


@router.get("/engines")
async def stream_engines():
    """
    SSE endpoint for real-time engine status updates.
    
    Usage:
        const es = new EventSource('http://localhost:8000/stream/engines');
        es.onmessage = (e) => console.log(JSON.parse(e.data));
    """
    return StreamingResponse(
        engine_status_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


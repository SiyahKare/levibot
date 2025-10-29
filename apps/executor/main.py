import os
import uuid

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from .adapters import adapter
from .chain import w3
from .routes import router

limiter = Limiter(key_func=get_remote_address)


class RequestIdMdw(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        request.state.rid = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response


def create_app() -> FastAPI:
    app = FastAPI(title="LeviBot API (miniface)", version="0.4")

    app.state.limiter = limiter
    app.add_middleware(RequestIdMdw)

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        return await limiter._slowapi_middleware(request, call_next)

    @app.exception_handler(Exception)
    async def boom(request: Request, exc: Exception):
        rid = getattr(request, "state", None) and request.state.rid or "-"
        return JSONResponse({"error": str(exc), "request_id": rid}, status_code=500)

    @app.get("/healthz")  # liveness
    def healthz():
        return {"ok": True}

    @app.get("/readyz")
    def readyz():
        if not os.getenv("RPC_BASE_SEPOLIA"):
            return {"ready": True, "mode": "mock"}
        try:
            h = w3.eth.block_number  # akses testi
            return {"ready": True, "mode": "real", "block": int(h)}
        except Exception as e:
            return JSONResponse({"ready": False, "error": str(e)}, status_code=503)

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    app.include_router(router, prefix="")
    app.include_router(adapter, prefix="")
    return app


def app() -> FastAPI:  # uvicorn --factory giriş noktası
    return create_app()

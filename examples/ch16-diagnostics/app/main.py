import logging
import os
import time
from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request

logger = logging.getLogger("diagnostics")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))


def dependency_ready() -> bool:
    return os.getenv("DEPENDENCY_READY", "false").lower() == "true"


def create_app(readiness_probe: Callable[[], bool] = dependency_ready) -> FastAPI:
    application = FastAPI(title="Chapter 16 diagnostics")

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        logger.info(
            "method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            (time.monotonic() - started) * 1000,
        )
        return response

    @application.get("/health/live")
    def live() -> dict[str, str]:
        return {"status": "alive"}

    @application.get("/health/ready")
    def ready() -> dict[str, str]:
        if not readiness_probe():
            raise HTTPException(status_code=503, detail="dependency unavailable")
        return {"status": "ready"}

    return application


app = create_app()

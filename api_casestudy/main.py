from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_casestudy.core.config import get_settings
from api_casestudy.routers import agent_router, health_router
import logging
import sys
import os
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse


def create_app() -> FastAPI:
    """
    Factory khởi tạo FastAPI cho dịch vụ CaseStudy Agent.
    """
    settings = get_settings()

    # Configure logging for this process so Render captures exception traces
    LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "DEBUG")
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.DEBUG),
        format="[%(levelname)s] %(asctime)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    app = FastAPI(
        title="CaseStudy Agent API",
        version=settings.version,
        description="Dịch vụ điều phối agent hội thoại cho từng case.",
    )

    app.include_router(agent_router, prefix="/api")
    app.include_router(health_router, prefix="/api")

    @app.middleware("http")
    async def _log_middleware(request: Request, call_next):
        logger = logging.getLogger("api.middleware")
        logger.debug("--> %s %s", request.method, request.url.path)
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error("Unhandled exception: %s", exc, exc_info=True)
            if os.getenv("APP_DEBUG_ERRORS", "1") == "1":
                tb = traceback.format_exc()
                return JSONResponse(status_code=500, content={"detail": str(exc), "traceback": tb})
            raise
        logger.debug("<-- %s %s %s", request.method, request.url.path, response.status_code)
        return response

    return app


app = create_app()
origins = [
    "http://localhost:8000",      # web chạy port 8000
    "http://127.0.0.1:8000",      # đôi khi trình duyệt dùng 127.0.0.1 thay vì localhost
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        # hoặc ["*"] nếu chỉ dev local
    allow_credentials=True,
    allow_methods=["*"],          # Cho phép GET, POST, OPTIONS,...
    allow_headers=["*"],          # Cho phép Content-Type, Authorization,...
)


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """
    Endpoint kiểm tra tình trạng chạy của service.
    """
    return {"status": "ok"}
